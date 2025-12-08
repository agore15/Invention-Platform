import argparse
import logging
import json
import hashlib
import time
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions, SetupOptions, WorkerOptions
from apache_beam.io import fileio

# Configuration (Hardcoded for Dataflow simplicity or passed via args)
PROJECT_ID = 'still-manifest-478014-c1'
REGION = 'us-central1'
BUCKET = 'invention-platform-data-001'
INPUT_PREFIX = f'gs://{BUCKET}/specs/processed/*.txt'
OUTPUT_PREFIX = f'gs://{BUCKET}/vector_search_staging/dataflow_output'

class ProcessSpec(beam.DoFn):
    """
    Reads a file, extracts metadata, and chunks the content using Spacy.
    """
    def setup(self):
        import spacy
        # Fallback if model not found, though requirements.txt should install it
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            from spacy.cli import download
            download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

    def process(self, readable_file):
        import re
        
        path = readable_file.metadata.path
        # file name like "38.211.txt"
        filename = path.split('/')[-1]
        spec_name = filename.replace('.txt', '')
        
        # Read content
        try:
            content = readable_file.read_utf8()
        except Exception as e:
            logging.error(f"Failed to read {path}: {e}")
            return

        metadata = {
            'source': f'3GPP TS {spec_name}',
            'gcs_uri': path,
            'type': 'Technical Specification'
        }

        doc = self.nlp(content[:1000000]) # Limit to 1MB per doc to avoid OOM in this simple version
        
        # Semantic Chunking (Simplistic for Dataflow stability)
        # Groups sentences into chunks ~500 chars
        current_chunk = []
        current_length = 0
        
        for sent in doc.sents:
            sent_text = sent.text.strip()
            if not sent_text:
                continue
                
            current_chunk.append(sent_text)
            current_length += len(sent_text)
            
            if current_length >= 500:
                chunk_text = " ".join(current_chunk)
                yield {
                    'text': chunk_text,
                    'metadata': metadata
                }
                current_chunk = []
                current_length = 0
        
        if current_chunk:
            yield {
                'text': " ".join(current_chunk),
                'metadata': metadata
            }

class GenerateEmbeddings(beam.DoFn):
    """
    Batches inputs and calls Vertex AI Embedding API.
    """
    def setup(self):
        from google.cloud import aiplatform
        from vertexai.preview.language_models import TextEmbeddingModel
        
        aiplatform.init(project=PROJECT_ID, location=REGION)
        self.model = TextEmbeddingModel.from_pretrained("text-embedding-004")

    def process(self, batch):
        # batch is a list of dicts {'text': ..., 'metadata': ...}
        if not batch:
            return

        texts = [item['text'] for item in batch]
        
        try:
            # Generate Embeddings
            embeddings = self.model.get_embeddings(texts)
            
            for i, emb in enumerate(embeddings):
                vector = emb.values
                original_item = batch[i]
                
                # Create Vector Search Datapoint (JSONL format)
                doc_id = hashlib.md5(original_item['text'].encode('utf-8')).hexdigest()
                
                record = {
                    'id': doc_id,
                    'embedding': vector,
                    'restricts': [
                        {'namespace': 'source', 'allow_list': [original_item['metadata'].get('source', 'unknown')]},
                        {'namespace': 'type', 'allow_list': [original_item['metadata'].get('type', 'TS')]}
                    ]
                }
                
                # Yield JSON string
                yield json.dumps(record)
                
        except Exception as e:
            logging.error(f"Embedding failed: {e}")
            # In production, output to Dead Letter Queue
            pass

def run(argv=None):
    parser = argparse.ArgumentParser()
    known_args, pipeline_args = parser.parse_known_args(argv)

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = True
    
    # Vertex AI Quota Safety: Limit workers
    worker_options = pipeline_options.view_as(WorkerOptions)
    worker_options.max_num_workers = 4 

    with beam.Pipeline(options=pipeline_options) as p:
        (
            p
            | 'MatchFiles' >> fileio.MatchFiles(INPUT_PREFIX)
            | 'ReadFiles' >> fileio.ReadMatches()
            | 'ChunkSpecs' >> beam.ParDo(ProcessSpec())
            | 'BatchForEmbedding' >> beam.BatchElements(min_batch_size=5, max_batch_size=20)
            | 'EmbedChunks' >> beam.ParDo(GenerateEmbeddings())
            | 'WriteJSONL' >> beam.io.WriteToText(OUTPUT_PREFIX, file_name_suffix='.json')
        )

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
