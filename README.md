# AI Study Assistant

An AI-powered learning assistant built using Streamlit and Google's Gemini API. This application helps users learn, understand study materials, generate quizzes, and create downloadable study notes through an interactive interface.

## Live Demo

**Live App:** [https://ai-study-assistant-xdcrvcd37tmawjfwcbgxqq.streamlit.app/]

**GitHub Repository:** [https://github.com/muthumani-7/AI-Study-Assistant]

## Features

- **AI Chat Assistant:** Ask questions and receive AI-generated responses.
- **Multiple Modes:** Personal Work, Study Help, and Coding Help.
- **PDF Reader:** Upload PDF documents and ask questions about their content.
- **Quiz Generator:** Generate quizzes, answer questions, view scores, and read explanations.
- **Study Notes Generator:** Create study notes and download them as text files.
- **Chat History:** Access previous conversations.
- **Responsive UI:** Use the application on desktop and mobile devices.

## Technology Stack

- Python
- Streamlit
- Google Gemini API
- Google Gen AI SDK
- PyPDF
- python-dotenv

## Project Structure

```text
AI-Study-Assistant/
├── app.py
├── requirements.txt
├── .gitignore
└── README.md
```

The `.env` file is used for local configuration and must not be committed to the public repository. Chat history files and other private data should also be excluded.

## Run Locally

### 1. Clone the repository

```bash
git clone 
https://github.com/muthumani-7/AI-Study-Assistant
cd AI-Study-Assistant
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the API key

Create a `.env` file in the project directory:

```text
GEMINI_API_KEY=your_api_key
```

Use your own valid Gemini API key. Never publish your API key.

### 4. Start the application

```bash
streamlit run app.py
```

Open the local URL shown in the terminal.

## Testing

The following features were tested successfully in the deployed application:

- Application launch and user interface
- Gemini AI responses
- Assistant modes
- Previous chat history
- PDF upload and question answering
- Quiz generation and scoring
- Study notes generation and download
- Mobile layout

## Learning Outcomes

- Integrating a generative AI API into a Python application
- Building interactive applications with Streamlit
- Processing PDF documents
- Managing application configuration and API credentials
- Deploying a Python application to the cloud
- Testing application features across devices

## Future Enhancements

- Support for additional document formats
- Persistent user accounts and cloud-based chat history
- More quiz customization options
- Improved document search and source references

## Author

**[MUTHUMANI K]**

GitHub: [https://github.com/muthumani-7]
