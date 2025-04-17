FROM ollama/ollama:latest

# Expose Ollama API port
EXPOSE 11434

# Set the command
CMD ["ollama", "serve"]