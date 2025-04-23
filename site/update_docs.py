import os
import subprocess
from pathlib import Path

def update_documentation():
    """Update MkDocs documentation and handle encoding issues"""
    try:
        # Convert all markdown files to UTF-8 and clean up temp files
        docs_dir = Path(__file__).parent
        for md_file in docs_dir.rglob('*.md'):
            try:
                # Skip temporary files
                if '_utf8.md' in str(md_file):
                    md_file.unlink()
                    continue
                    
                content = md_file.read_bytes()
                md_file.write_text(content.decode('utf-8', errors='replace'), encoding='utf-8')
            except Exception as e:
                print(f"Error converting {md_file}: {str(e)}")

        # Clean up site directory before building
        site_dir = docs_dir.parent / 'site'
        if site_dir.exists():
            try:
                for item in site_dir.glob('*'):
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
            except Exception as e:
                print(f"Warning: Could not clean site directory: {str(e)}")

        # Build docs with limited memory usage
        os.chdir(str(docs_dir.parent))
        subprocess.run(['mkdocs', 'build', '--clean'], check=True)
        
        # Fix common broken links
        fix_broken_links(docs_dir)
        
        # Build and serve docs
        os.chdir(str(docs_dir.parent))
        subprocess.run(['mkdocs', 'build'], check=True)
        print("Documentation updated successfully!")
        
    except Exception as e:
        print(f"Failed to update documentation: {str(e)}")

def fix_broken_links(docs_dir):
    """Fix common broken links in documentation"""
    # Add cleanup of empty files
    for md_file in docs_dir.rglob('*.md'):
        if md_file.stat().st_size == 0:
            md_file.unlink()
    
    # Create missing directories
    (docs_dir / 'user-guide').mkdir(exist_ok=True)
    (docs_dir / 'development').mkdir(exist_ok=True)
    
    # Create placeholder files for missing targets
    placeholder_files = [
        'user-guide/faq.md',
        'user-guide/index.md',
        'development/index.md',
        'architecture/index.md'
    ]
    
    for file in placeholder_files:
        path = docs_dir / file
        if not path.exists():
            path.write_text(f"# {path.stem}\n\nPlaceholder content", encoding='utf-8')

if __name__ == '__main__':
    update_documentation()