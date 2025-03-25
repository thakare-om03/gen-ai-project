#chains.py

import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from dotenv import load_dotenv

load_dotenv()

class Chain:
    def __init__(self, api_key=None):
        self.llm = ChatGroq(
            temperature=1,
            groq_api_key=api_key or os.getenv("GROQ_API_KEY"),
            model_name="llama-3.3-70b-versatile"
        )

    def extract_jobs(self, cleaned_text):
        prompt_extract = PromptTemplate.from_template(
            """
            ### SCRAPED TEXT FROM WEBSITE:
            {page_data}
            ### INSTRUCTION:
            The scraped text is from the career's page of a website.
            Your job is to extract the job postings and return them in JSON format containing the following keys: `role`, `experience`, `skills` and `description`.
            Only return the valid JSON.
            ### VALID JSON (NO PREAMBLE):
            """
        )
        chain_extract = prompt_extract | self.llm
        res = chain_extract.invoke(input={"page_data": cleaned_text})
        try:
            json_parser = JsonOutputParser()
            res = json_parser.parse(res.content)
        except OutputParserException:
            raise OutputParserException("Context too big. Unable to parse jobs.")
        return res if isinstance(res, list) else [res]

    def write_mail(self, job, links, email_length="Medium", company_name="TCS", sender_name="Om Thakare"):
        # Different length templates
        length_instructions = {
            "Short": "Create a brief, concise cold email (around 150 words) that's straight to the point.",
            "Medium": "Create a balanced cold email (around 250 words) with enough detail to be persuasive.",
            "Long": "Create a comprehensive cold email (around 350 words) with detailed examples and value propositions."
        }
        
        prompt_email = PromptTemplate.from_template(
            """
            ### JOB DESCRIPTION:
            {job_description}

            ### INSTRUCTION:
            You are {sender_name}, a business development executive at {company_name}. {company_name} is an AI & Software Consulting company dedicated to facilitating
            the seamless integration of business processes through automated tools. 
            Over our experience, we have empowered numerous enterprises with tailored solutions, fostering scalability, 
            process optimization, cost reduction, and heightened overall efficiency. 
            
            {length_instruction}
            
            Your job is to write a cold email to the client regarding the job mentioned above describing the capability of {company_name} 
            in fulfilling their needs.
            Also add the most relevant ones from the following links to showcase {company_name}'s portfolio: {link_list}
            
            Remember you are {sender_name}, HR at {company_name}.
            
            Format the email properly with:
            1. A clear subject line starting with "Subject: "
            2. Professional greeting
            3. Well-structured paragraphs with proper spacing between them
            4. A call to action
            5. Professional closing
            6. Your name and title in the signature
            
            Do not provide a preamble.
            ### EMAIL (NO PREAMBLE):

            """
        )
        chain_email = prompt_email | self.llm
        res = chain_email.invoke({
            "job_description": str(job), 
            "link_list": links,
            "length_instruction": length_instructions.get(email_length, length_instructions["Medium"]),
            "company_name": company_name,
            "sender_name": sender_name
        })
        return res.content

if __name__ == "__main__":
    print(os.getenv("GROQ_API_KEY"))