# Use the official Playwright image which has all browser dependencies
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOME=/home/user
ENV PATH="/home/user/.local/bin:${PATH}"

# Create and switch to a non-root user
RUN useradd -m -u 1000 user
USER user
WORKDIR $HOME/app

# Copy requirements and install
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Install patchright browsers (using the pre-installed dependencies from the base image)
RUN python3 -m patchright install chromium

# Copy the rest of the application
COPY --chown=user . .

# Expose Hugging Face standard port
EXPOSE 7860

# Command to run the application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
