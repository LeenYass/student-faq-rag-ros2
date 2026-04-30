# Student FAQ RAG Robot (ROS2)

## Part 1 – RAG System
Implements a Retrieval-Augmented Generation system using:
- FAISS
- Sentence Transformers
- Ollama (qwen2.5:0.5b)

Answers university student FAQ questions using local documents.

## Part 2 – ROS2 Integration
Integrates the RAG system into a robot pipeline using ROS2:
- Subscribes to `words` (Whisper output)
- Publishes to `ollama_reply`
- Uses gTTS for speech output

## Pipeline
Speech → Whisper → RAG → Ollama → gTTS → Speaker
