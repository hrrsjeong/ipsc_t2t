import subprocess
import argparse
import os

def run_minimap2(target_fasta, query_fasta, output_paf):
    """Runs minimap2 for whole-genome alignment with -K 4G option.

    Args:
        target_fasta (str): Path to the target (reference) FASTA file (hg38).
        query_fasta (str): Path to the query (de novo assembly) FASTA file.
        output_paf (str): Path to the output PAF file.
    """
    try:
        command = [
            "minimap2",
            "-ax", "asm5",  # Recommended preset for assembly-to-reference alignment
            "-secondary=no",  # Suppress secondary alignments
            "-K", "4G",      # Added option for larger k-mer table
            target_fasta,
            query_fasta,
            "-o", output_paf
        ]
        print(f"Running command: {' '.join(command)}")
        subprocess.run(command, check=True)
        print(f"Successfully generated PAF file: {output_paf}")
    except subprocess.CalledProcessError as e:
        print(f"Error running minimap2: {e}")
    except FileNotFoundError:
        print("Error: minimap2 not found in your PATH. Please ensure it is installed.")

def process_directories(target_fasta, input_dir, output_dir):
    """Processes all FASTA files in the input directory and runs minimap2.

    Args:
        target_fasta (str): Path to the target (reference) FASTA file (hg38).
        input_dir (str): Path to the directory containing the de novo assembly FASTA files.
        output_dir (str): Path to the directory where the output PAF files will be saved.
    """
    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        return

    os.makedirs(output_dir, exist_ok=True)
    print(f"Processing FASTA files in: {input_dir}")
    print(f"Outputting PAF files to: {output_dir}")

    for filename in os.listdir(input_dir):
        if filename.endswith(".fasta") or filename.endswith(".fa") or filename.endswith(".fna"):
            query_fasta_path = os.path.join(input_dir, filename)
            base_name = os.path.splitext(filename)[0]
            output_paf_path = os.path.join(output_dir, f"{base_name}_vs_hg38.paf")
            print(f"Aligning '{filename}'...")
            run_minimap2(target_fasta, query_fasta_path, output_paf_path)
            print("-" * 30)

def main():
    parser = argparse.ArgumentParser(description="Run whole-genome alignment using minimap2 on FASTA files in a directory.")
    parser.add_argument("target_fasta", help="Path to the target (reference) FASTA file (hg38).")
    parser.add_argument("input_dir", help="Path to the directory containing the de novo assembly FASTA files.")
    parser.add_argument("output_dir", help="Path to the directory where the output PAF files will be saved.")

    args = parser.parse_args()

    process_directories(args.target_fasta, args.input_dir, args.output_dir)

if __name__ == "__main__":
    main()
