# Use the official Playwright image
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/user
ENV PATH="/home/user/.local/bin:${PATH}"

# Use the existing user with UID 1000 (usually 'pwuser' or 'ubuntu' in this image)
# We just create the directory and set permissions
WORKDIR $HOME/app

# Install dependencies as root
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN python3 -m patchright install chromium

# Copy application code
COPY . .

# Ensure the user 1000 has access to the files
RUN chown -R 1000:1000 $HOME

# Switch to UID 1000 (Hugging Face default)
USER 1000

# Expose Hugging Face standard port
EXPOSE 7860

# Command to run the application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
