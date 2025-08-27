FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY app.py .

# Install dependencies directly
RUN pip install flask>=2.3.0 redis>=4.5.0

# Expose port
EXPOSE 5000

# Set max string digits for large Fibonacci numbers
ENV PYTHONINTMAXSTRDIGITS=0

# Run the application
CMD ["python", "app.py"]
