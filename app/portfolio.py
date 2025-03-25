#portfolio.py

import os
import pandas as pd
import chromadb
import uuid


class Portfolio:
    def __init__(self, file_path=None):
        self.file_path = file_path or os.path.join(os.path.dirname(os.path.dirname(__file__)), "my_portfolio.csv")
        try:
            self.data = pd.read_csv(self.file_path)
        except:
            self.data = pd.DataFrame(columns=["Techstack", "Links"])
            
        self.chroma_client = chromadb.PersistentClient(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vectorstore'))
        self.collection = self.chroma_client.get_or_create_collection(name="portfolio")

    def load_portfolio(self):
        """Load portfolio data into vector database"""
        if not self.collection.count() or self.collection.count() != len(self.data):
            self.reset_collection()
            for _, row in self.data.iterrows():
                self.collection.add(documents=row["Techstack"],
                                    metadatas={"links": row["Links"]},
                                    ids=[str(uuid.uuid4())])
    
    def reset_collection(self):
        """Reset the collection"""
        try:
            self.chroma_client.delete_collection(name="portfolio")
        except:
            pass
        self.collection = self.chroma_client.get_or_create_collection(name="portfolio")

    def query_links(self, skills, n_results=2):
        """Query for relevant portfolio links based on skills"""
        if not skills:
            return []
        
        # If skills is a string, convert to list
        if isinstance(skills, str):
            skills = [skills]
            
        results = self.collection.query(query_texts=skills, n_results=n_results)
        return results.get('metadatas', [])
    
    def add_item(self, techstack, link):
        """Add a new item to the portfolio"""
        new_row = pd.DataFrame({"Techstack": [techstack], "Links": [link]})
        self.data = pd.concat([self.data, new_row], ignore_index=True)
        self.data.to_csv(self.file_path, index=False)
        
        # Update vector database
        self.collection.add(
            documents=[techstack],
            metadatas=[{"links": link}],
            ids=[str(uuid.uuid4())]
        )
        
        return True
    
    def remove_item(self, index):
        """Remove an item from the portfolio"""
        if index >= 0 and index < len(self.data):
            self.data = self.data.drop(index).reset_index(drop=True)
            self.data.to_csv(self.file_path, index=False)
            
            # Reset and reload vector database
            self.reset_collection()
            self.load_portfolio()
            
            return True
        return False
