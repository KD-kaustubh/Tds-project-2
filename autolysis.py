import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import argparse
import openai  # Make sure you install this library: pip install openai

# Function to analyze the data (basic summary stats, missing values, correlation matrix)
def analyze_data(df):
    # Summary statistics for numerical columns
    summary_stats = df.describe()

    # Check for missing values
    missing_values = df.isnull().sum()

    # Select only numeric columns for correlation matrix
    numeric_df = df.select_dtypes(include=[np.number])

    # Correlation matrix for numerical columns
    corr_matrix = numeric_df.corr() if not numeric_df.empty else pd.DataFrame()

    return summary_stats, missing_values, corr_matrix


# Function to detect outliers using the IQR method
def detect_outliers(df):
    # Select only numeric columns
    df_numeric = df.select_dtypes(include=[np.number])

    # Apply the IQR method to find outliers in the numeric columns
    Q1 = df_numeric.quantile(0.25)
    Q3 = df_numeric.quantile(0.75)
    IQR = Q3 - Q1
    outliers = ((df_numeric < (Q1 - 1.5 * IQR)) | (df_numeric > (Q3 + 1.5 * IQR))).sum()

    return outliers


# Function to generate visualizations (correlation heatmap, outliers plot, and distribution plot)
def visualize_data(corr_matrix, outliers, df, output_dir):
    # Generate a heatmap for the correlation matrix
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
    plt.title('Correlation Matrix')
    heatmap_file = os.path.join(output_dir, 'correlation_matrix.png')
    plt.savefig(heatmap_file)
    plt.close()

    # Check if there are outliers to plot
    if not outliers.empty and outliers.sum() > 0:
        # Plot the outliers
        plt.figure(figsize=(10, 6))
        outliers.plot(kind='bar', color='red')
        plt.title('Outliers Detection')
        plt.xlabel('Columns')
        plt.ylabel('Number of Outliers')
        outliers_file = os.path.join(output_dir, 'outliers.png')
        plt.savefig(outliers_file)
        plt.close()
    else:
        print("No outliers detected to visualize.")
        outliers_file = None  # No file created for outliers

    # Generate a distribution plot for the first numeric column
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    if len(numeric_columns) > 0:
        first_numeric_column = numeric_columns[0]  # Get the first numeric column
        plt.figure(figsize=(10, 6))
        sns.histplot(df[first_numeric_column], kde=True, color='blue', bins=30)
        plt.title(f'Distribution')
        dist_plot_file = os.path.join(output_dir, f'distribution_.png')
        plt.savefig(dist_plot_file)
        plt.close()
    else:
        dist_plot_file = None  # No numeric columns to plot

    return heatmap_file, outliers_file, dist_plot_file


# Function to create the README.md with a narrative and visualizations
def create_readme(summary_stats, missing_values, corr_matrix, outliers, output_dir):
    # Write the analysis report to a markdown file
    readme_file = os.path.join(output_dir, 'README.md')
    try:
        with open(readme_file, 'w') as f:
            f.write("# Automated Data Analysis Report\n\n")
            f.write("## Summary Statistics\n")
            f.write(f"{summary_stats}\n\n")

            f.write("## Missing Values\n")
            f.write(f"{missing_values}\n\n")

            f.write("## Outliers Detection\n")
            f.write(f"{outliers}\n\n")

            f.write("## Correlation Matrix\n")
            f.write("Below is the correlation matrix of numerical features:\n\n")
            f.write("![Correlation Matrix](correlation_matrix.png)\n\n")

            f.write("## Outliers Visualization\n")
            f.write("Below is the outliers detection chart:\n\n")
            f.write("![Outliers](outliers.png)\n")

            f.write("## Distribution\n")
            f.write("Below is the distribution plot :\n\n")
            f.write("![Distribution](distribution_.png)\n")  # Placeholder for distribution plot

        return readme_file
    except Exception as e:
        print(f"Error writing to README.md: {e}")
        return None


# Function to generate a detailed story using the new OpenAI API through the proxy
def question_llm(prompt, context):
    try:
        # Set OpenAI API key
        openai.api_key = os.getenv("AIPROXY_TOKEN")

        # Set the custom API base URL for AI Proxy (ensure there's no trailing slash)
        openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"  # Corrected endpoint

        # Enhance the prompt to ask for a more detailed story with paragraphs and necessary structure
        full_prompt = f"""
        Based on the following data analysis, please generate a creative and engaging story. The story should include multiple paragraphs, a clear structure with an introduction, body, and conclusion, and should feel like a well-rounded narrative.

        Context:
        {context}

        Data Analysis Prompt:
        {prompt}

        The story should be elaborate and cover the following:
        - An introduction to set the context.
        - A detailed body that expands on the data points and explores their significance.
        - A conclusion that wraps up the analysis and presents any potential outcomes or lessons.
        - Use transitions to connect ideas and keep the narrative flowing smoothly.
        - Format the story with clear paragraphs and structure.
        """

        # Request to AI Proxy's chat completions endpoint for gpt-4o-mini model
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Using GPT-4o-Mini model
            messages=[ 
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=1000,  # Increased max_tokens for longer output
            temperature=0.7,
        )

        # Extract the generated text from the response
        story = response['choices'][0]['message']['content'].strip()

        return story

    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return "Failed to generate story."


# Main function that integrates all the steps
def main(csv_file, api_token):
    # Set the API token as an environment variable
    os.environ["AIPROXY_TOKEN"] = api_token  # Set token as environment variable

    # Try reading the CSV file with 'ISO-8859-1' encoding to handle special characters
    try:
        df = pd.read_csv(csv_file, encoding='ISO-8859-1')
    except UnicodeDecodeError as e:
        print(f"Error reading file: {e}")
        return

    # Analyze the data: summary statistics, missing values, correlation matrix
    summary_stats, missing_values, corr_matrix = analyze_data(df)

    # Detect outliers
    outliers = detect_outliers(df)

    # Create the output directory if it doesn't exist
    output_dir = os.path.splitext(csv_file)[0]
    os.makedirs(output_dir, exist_ok=True)

    # Visualize the data
    heatmap_file, outliers_file, dist_plot_file = visualize_data(corr_matrix, outliers, df, output_dir)

    # Generate the story using the LLM
    story = question_llm("Generate a nice and creative story from the analysis", 
                         context=f"Dataset Analysis:\nSummary Statistics:\n{summary_stats}\n\nMissing Values:\n{missing_values}\n\nCorrelation Matrix:\n{corr_matrix}\n\nOutliers:\n{outliers}")

    # Create the README.md file with the analysis and the story
    readme_file = create_readme(summary_stats, missing_values, corr_matrix, outliers, output_dir)

    if readme_file:
        try:
            # Append the story to the README.md file
            with open(readme_file, 'a') as f:
                f.write("## Story\n")
                f.write(f"{story}\n")

            print(f"Analysis complete! Results saved in '{output_dir}' directory.")
            print(f"README file: {readme_file}")
            print(f"Visualizations: {heatmap_file}, {outliers_file}, {dist_plot_file}")
        except Exception as e:
            print(f"Error appending story to README.md: {e}")
    else:
        print("Error generating the README.md file.")


if __name__ == "__main__":
    # Command-line argument parsing
    parser = argparse.ArgumentParser(description="Automated Data Analysis")
    parser.add_argument("csv_file", help="CSV file for analysis")
    parser.add_argument("api_token", help="API token for authentication")  # Added API token argument
    args = parser.parse_args()

    # Run the main function with the provided CSV file and API token
    main(args.csv_file, args.api_token)
