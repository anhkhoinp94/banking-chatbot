FROM ollama/ollama:latest

RUN ollama serve > /tmp/ollama.log 2>&1 & \
    sleep 5 && \
    ollama pull qwen2.5:3b && \
    ollama pull nomic-embed-text

EXPOSE 11434

ENTRYPOINT ["ollama", "serve"]
