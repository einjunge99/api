# Sign Language API

This project is a FastAPI-based application designed to provide services for sign language learning. The application can be containerized using Docker and uploaded to Google Cloud's Artifact Registry.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the API](#running-the-api)
- [Building and Pushing Docker Image](#building-and-pushing-docker-image)
  - [Step 1: Authenticate with Google Cloud](#step-1-authenticate-with-google-cloud)
  - [Step 2: Build the Docker Image](#step-2-build-the-docker-image)
  - [Step 3: Tag the Docker Image](#step-3-tag-the-docker-image)
  - [Step 4: Push the Docker Image](#step-4-push-the-docker-image)

## Prerequisites

Before you begin, ensure you have the following installed on your machine:

- [Docker](https://docs.docker.com/get-docker/)
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- [Python 3.7+](https://www.python.org/downloads/)
- [FastAPI](https://fastapi.tiangolo.com/) and other dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/sign-language-api.git
   cd sign-language-api
   ```

2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the API

To run the API locally, execute the following command:

```bash
uvicorn main:app --reload
```

The API will be accessible at `http://127.0.0.1:8000`.

## Building and Pushing Docker Image

### Step 1: Authenticate with Google Cloud

First, authenticate your Docker client to your Google Cloud project:

```bash
gcloud auth login
gcloud auth configure-docker us-west4-docker.pkg.dev
```

### Step 2: Build the Docker Image

Build the Docker image with the following command:

```bash
docker build --platform linux/amd64 -t sign-language-api .
```

### Step 3: Tag the Docker Image

Tag the Docker image to prepare it for uploading to Google Cloud Artifact Registry:

```bash
docker tag sign-language-api us-west4-docker.pkg.dev/sign-language-learning/sign-language/sign-language-api:latest
```

### Step 4: Push the Docker Image

Finally, push the Docker image to the registry:

```bash
docker push us-west4-docker.pkg.dev/sign-language-learning/sign-language/sign-language-api:latest
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## Contact

If you have any questions or suggestions, feel free to open an issue or reach out to the project maintainers.

---

**Note:** Replace placeholder URLs and project-specific information as necessary.
