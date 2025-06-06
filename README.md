# Acarelia

Acarelia is a web-based platform designed to evaluate the credibility of academic authors based on their Google Scholar publications. Users can search for an author’s name and receive an automated analysis of their work, including:

- AI generation detection
- Plagiarism checks
- Grammar and writing style evaluation

## Features

- **Author Search**: Enter an author’s name to retrieve publication data.
- **AI Detection**: Analyze text for signs of automated or AI-assisted writing.
- **Plagiarism Checking**: Compare publications against known sources to identify potential overlap.

## Architecture

Acarelia follows a microservices approach, with separate services handling tasks such as:
- Retrieving publication data (scholar-scraper)
- Resolving DOIs (doi-resolver)
- Checking for plagiarism (plagiarism-checker)
- Performing AI-based text analysis (ai-analyzer)
- Coordinating requests through a gateway API