from langchain.llms import OpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.vectorstores import FAISS
from ..config.config import Config
import pytesseract
from PIL import Image
import io
import logging

class LangchainService:
    @staticmethod
    def create_embeddings(text_content):
        try:
            embeddings = OpenAIEmbeddings(openai_api_key=Config.OPENAI_KEY)
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            texts = text_splitter.split_text(text_content)
            vectorstore = FAISS.from_texts(texts, embeddings)
            return vectorstore
        except Exception as e:
            logging.error(f"Error creating embeddings: {str(e)}")
            return None

    @staticmethod
    def query_document(vectorstore, query):
        try:
            llm = OpenAI(temperature=0, openai_api_key=Config.OPENAI_KEY)
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever()
            )
            response = qa_chain.run(query)
            return response
        except Exception as e:
            logging.error(f"Error querying document: {str(e)}")
            return None

    @staticmethod
    def summarize_text(text_content):
        try:
            llm = OpenAI(temperature=0.3, openai_api_key=Config.OPENAI_KEY)
            prompt = f"Please summarize the following text:\n\n{text_content}"
            response = llm.predict(prompt)
            return response
        except Exception as e:
            logging.error(f"Error summarizing text: {str(e)}")
            return None

    @staticmethod
    def extract_text_from_image(image_data, lang='eng'):
        try:
            # Convert bytes to PIL Image
            if isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
            else:
                image = Image.open(image_data)

            # Extract text using pytesseract
            text = pytesseract.image_to_string(image, lang=lang)
            
            # Clean up the extracted text
            text = text.strip()
            
            return text
        except Exception as e:
            logging.error(f"Error in OCR process: {str(e)}")
            return None

    @staticmethod
    def extract_text_with_layout(image_data, lang='eng'):
        try:
            if isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
            else:
                image = Image.open(image_data)

            # Get detailed OCR data including position information
            ocr_data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
            
            # Process the OCR data to maintain layout
            text_blocks = []
            for i in range(len(ocr_data['text'])):
                if int(ocr_data['conf'][i]) > 60:  # Filter low confidence results
                    text = ocr_data['text'][i].strip()
                    if text:
                        text_blocks.append({
                            'text': text,
                            'left': ocr_data['left'][i],
                            'top': ocr_data['top'][i],
                            'width': ocr_data['width'][i],
                            'height': ocr_data['height'][i]
                        })
            
            return text_blocks
        except Exception as e:
            logging.error(f"Error in OCR layout process: {str(e)}")
            return None