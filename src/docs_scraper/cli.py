"""
Command line interface for the docs_scraper package.
"""
import logging

def main():
    """Entry point for the package when run from the command line."""
    from docs_scraper.server import main as server_main
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the server
    server_main()

if __name__ == "__main__":
    main() 