import subprocess
import argparse
import os
import pandas as pd

def run_paf2liftover(paf_file, chain_file):
    """Converts a PAF file to a chain file using paf2liftover.py.

    Args:
        paf_file (str): Path to the input PAF file.
        chain_file (str): Path to the output chain file.
    """
    try:
        command = [
            "paf2liftover.py",
            "--no-chains",  # Exclude chain format output
            "--best-only",  # Keep only the best alignment for each query
            paf_file,
            chain_file + ".tmp"  # Temporary output before filtering
        ]
        print(f"Running paf2liftover.py (best-only) for: {paf_file}")
        subprocess.run(command, check=True, capture_output=True, text=True)

        # Filter the temporary output to create the final chain file
        with open(chain_file + ".tmp", "r") as infile, open(chain_file, "w") as outfile:
            for line in infile:
                if not line.startswith("#") and line.strip():  # Skip comments and empty lines
                    parts = line.split('\t')
                    if len(parts) == 13:  # Basic chain format with single mapping
                        outfile.write(line)

        os.remove(chain_file + ".tmp")
        print(f"Successfully generated filtered chain file: {chain_file}")

    except subprocess.CalledProcessError as e:
        print(f"Error running paf2liftover.py: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
    except FileNotFoundError:
        print("Error: paf2liftover.py not found in your PATH. "
              "Make sure the cactus toolkit is installed and the script is accessible.")

def run_liftover(bed_file, chain_file, output_bed, unmapped_bed):
    """Runs the liftOver utility.

    Args:
        bed_file (str): Path to the input BED file (hg38 imprinted loci).
        chain_file (str): Path to the chain file.
        output_bed (str): Path to the output BED file with lifted-over coordinates.
        unmapped_bed (str): Path to the output BED file for unmapped intervals.
    """
    try:
        command = [
            "liftOver",
            bed_file,
            chain_file,
            output_bed,
            unmapped_bed
        ]
        print(f"Running liftOver for chain file: {chain_file}")
        subprocess.run(command, check=True)
        print(f"Successfully generated lifted-over BED file: {output_bed}")
        if os.path.exists(unmapped_bed) and os.stat(unmapped_bed).st_size > 0:
            print(f"Unmapped intervals saved to: {unmapped_bed}")
        else:
            print("No intervals were unmapped.")
    except subprocess.CalledProcessError as e:
        print(f"Error running liftOver: {e}")
    except FileNotFoundError:
        print("Error: liftOver not found in your PATH. "
              "Make sure the UCSC Genome Browser utilities are installed and liftOver is accessible.")

def create_hg38_bed(imprinted_loci_tsv, output_bed):
    """Creates a BED file from the imprinted loci TSV file (assuming hg38 coordinates).

    Args:
        imprinted_loci_tsv (str): Path to the Imprinted_DMR_List_V1.tsv file.
        output_bed (str): Path to the output BED file.
    """
    try:
        df = pd.read_csv(imprinted_loci_tsv, sep='\t')
        bed_df = df[['Chromosome', 'Start', 'End']].copy()
        bed_df['Chromosome'] = 'chr' + bed_df['Chromosome'].astype(str)
        bed_df.to_csv(output_bed, sep='\t', header=False, index=False)
        print(f"Successfully created hg38 BED file: {output_bed}")
        return output_bed
    except FileNotFoundError:
        print(f"Error: Imprinted loci TSV file not found: {imprinted_loci_tsv}")
    except KeyError as e:
        print(f"Error: Required column not found in TSV file: {e}. "
              "Please ensure the TSV has 'Chromosome', 'Start', and 'End' columns.")
    return None

def process_paf_directory(paf_dir, output_bed_dir, unmapped_bed_dir, hg38_bed_file):
    """Processes all PAF files in the given directory."""
    for filename in os.listdir(paf_dir):
        if filename.endswith(".paf"):
            assembly_name = filename.replace(".paf", "")
            paf_file = os.path.join(paf_dir, filename)
            chain_file = os.path.join(output_bed_dir, f"{assembly_name}_to_hg38.chain")
            lifted_over_bed = os.path.join(output_bed_dir, f"{assembly_name}_imprinted_loci.bed")
            unmapped_bed = os.path.join(unmapped_bed_dir, f"{assembly_name}_unmapped.bed")

            # Run paf2liftover with options to handle one-to-many/many-to-one
            run_paf2liftover(paf_file, chain_file)

            # Run liftOver
            if os.path.exists(chain_file):
                run_liftover(hg38_bed_file, chain_file, lifted_over_bed, unmapped_bed)
            else:
                print(f"Chain file not generated for {assembly_name}. Skipping liftOver.")

def main():
    parser = argparse.ArgumentParser(description="Liftover hg38 imprinted loci coordinates to de novo assemblies using PAF alignments, handling one-to-many mappings.")
    parser.add_argument("paf_dir", help="Directory containing the PAF files.")
    parser.add_argument("output_bed_dir", help="Directory to save the lifted-over BED files.")
    parser.add_argument("unmapped_bed_dir", help="Directory to save the unmapped intervals BED files.")
    parser.add_argument("imprinted_loci_tsv", help="Path to the Imprinted_DMR_List_V1.tsv file (hg38 coordinates).")

    args = parser.parse_args()

    os.makedirs(args.output_bed_dir, exist_ok=True)
    os.makedirs(args.unmapped_bed_dir, exist_ok=True)

    # Create hg38 BED file
    hg38_bed_file = os.path.join(os.getcwd(), "hg38_imprinted_loci.bed")
    hg38_bed_file = create_hg38_bed(args.imprinted_loci_tsv, hg38_bed_file)
    if not hg38_bed_file:
        return

    # Process all PAF files in the specified directory
    process_paf_directory(args.paf_dir, args.output_bed_dir, args.unmapped_bed_dir, hg38_bed_file)

    # Clean up the temporary hg38 BED file
    if os.path.exists(hg38_bed_file):
        os.remove(hg38_bed_file)

if __name__ == "__main__":
    main()
