import json
import os
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple

import ipywidgets as widgets
import pandas as pd
from IPython.display import HTML, clear_output, display

from db.db_postgres import get_db_connection


@dataclass
class SentimentExample:
    content: str
    positive: float
    negative: float
    helpful: float
    sarcastic: float
    category: str
    message_id: Optional[int] = None
    notes: Optional[str] = None

class SentimentTuningNotebook:
    def __init__(self, examples_file: str = 'sentiment_examples.json'):
        self.examples_file = examples_file
        self.examples: List[SentimentExample] = []
        self.current_df = None
        self.selected_message_id = None
        self.load_examples()
        self.setup_widgets()
        
    def load_examples(self):
        if os.path.exists(self.examples_file):
            with open(self.examples_file, 'r') as f:
                data = json.load(f)
                self.examples = [SentimentExample(**example) for example in data]
    
    def save_examples(self):
        with open(self.examples_file, 'w') as f:
            json.dump([asdict(example) for example in self.examples], f, indent=2)
    
    def setup_widgets(self):
        """Initialize all widgets."""
        # Main action selector
        self.action_dropdown = widgets.Dropdown(
            options=['View Top Positive', 'View Top Negative', 'View Examples', 'Generate Prompt'],
            description='Action:',
            style={'description_width': 'initial'}
        )
        
        # Message selector
        self.message_selector = widgets.Select(
            options=[],
            description='Select message:',
            disabled=False,
            layout={'width': 'auto', 'height': '400px'}
        )
        
        # Notes input
        self.notes_input = widgets.Textarea(
            description='Notes:',
            disabled=False,
            layout={'width': 'auto', 'height': '100px'}
        )
        
        # Category selector
        self.category_dropdown = widgets.Dropdown(
            options=['positive', 'negative', 'helpful', 'sarcastic'],
            description='Category:',
            style={'description_width': 'initial'}
        )
        
        # Save button
        self.save_button = widgets.Button(
            description='Save as Example',
            button_style='success',
            disabled=True
        )
        
        # Message details
        self.message_details = widgets.HTML(value='')
        
        # Set up callbacks
        self.action_dropdown.observe(self.handle_action_change, names='value')
        self.message_selector.observe(self.handle_message_select, names='value')
        self.save_button.on_click(self.handle_save)
        
        # Layout
        self.input_container = widgets.VBox([
            self.notes_input,
            widgets.HBox([self.category_dropdown, self.save_button])
        ])
        self.input_container.layout.visibility = 'hidden'
        
        # Container for dynamic content
        self.output = widgets.Output()
    
    def get_top_messages(self, sentiment_type: str = 'positive', limit: int = 50) -> pd.DataFrame:
        """Get top messages by sentiment score."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            column = f"sentiment_{sentiment_type}"
            ordering = "DESC" if sentiment_type == 'positive' else "ASC"
            
            cursor.execute(f"""
                SELECT 
                    message_id,
                    content,
                    sentiment_positive,
                    sentiment_negative,
                    sentiment_helpful,
                    sentiment_sarcastic
                FROM telegram_messages
                WHERE sentiment_analyzed = TRUE
                AND length(content) > 10
                ORDER BY {column} {ordering}
                LIMIT %s
            """, (limit,))
            
            results = cursor.fetchall()
            return pd.DataFrame(results, columns=[
                'ID', 'Content', 'Positive', 'Negative', 'Helpful', 'Sarcastic'
            ])
            
        except Exception as e:
            print(f"Error fetching top messages: {e}")
            return pd.DataFrame()
        finally:
            cursor.close()
            conn.close()
    
    def handle_action_change(self, change):
        """Handle changes to the action dropdown."""
        if change['type'] == 'change' and change['name'] == 'value':
            with self.output:
                clear_output()
                
                if change['new'] in ['View Top Positive', 'View Top Negative']:
                    sentiment_type = 'positive' if change['new'] == 'View Top Positive' else 'negative'
                    self.current_df = self.get_top_messages(sentiment_type)
                    
                    # Update message selector options
                    self.message_selector.options = [
                        (f"[{row['Positive']:.2f}/{row['Negative']:.2f}] {row['Content'][:100]}...", row['ID'])
                        for _, row in self.current_df.iterrows()
                    ]
                    
                    display(widgets.VBox([
                        self.message_selector,
                        self.message_details,
                        self.input_container
                    ]))
                    
                elif change['new'] == 'View Examples':
                    if self.examples:
                        df = pd.DataFrame([asdict(ex) for ex in self.examples])
                        display(HTML(df.to_html()))
                    else:
                        print("No examples yet.")
                        
                elif change['new'] == 'Generate Prompt':
                    print(self.generate_system_prompt())
    
    def handle_message_select(self, change):
        """Handle message selection."""
        if change['type'] == 'change' and change['name'] == 'value':
            if change['new']:
                self.selected_message_id = change['new']
                row = self.current_df[self.current_df['ID'] == change['new']].iloc[0]
                
                # Update message details display
                details = f"""
                <div style='padding: 10px; background-color: #f0f0f0; border-radius: 5px;'>
                    <p><strong>Content:</strong> {row['Content']}</p>
                    <p><strong>Scores:</strong></p>
                    <ul>
                        <li>Positive: {row['Positive']:.3f}</li>
                        <li>Negative: {row['Negative']:.3f}</li>
                        <li>Helpful: {row['Helpful']:.3f}</li>
                        <li>Sarcastic: {row['Sarcastic']:.3f}</li>
                    </ul>
                </div>
                """
                self.message_details.value = details
                
                # Show input container
                self.input_container.layout.visibility = 'visible'
                self.save_button.disabled = False
    
    def handle_save(self, b):
        """Handle saving message as example."""
        if self.selected_message_id:
            row = self.current_df[self.current_df['ID'] == self.selected_message_id].iloc[0]
            
            self.add_example(
                content=row['Content'],
                scores={
                    'positive': row['Positive'],
                    'negative': row['Negative'],
                    'helpful': row['Helpful'],
                    'sarcastic': row['Sarcastic']
                },
                category=self.category_dropdown.value,
                message_id=row['ID'],
                notes=self.notes_input.value
            )
            
            # Clear inputs
            self.notes_input.value = ''
            self.message_selector.value = None
            self.message_details.value = ''
            self.input_container.layout.visibility = 'hidden'
            self.save_button.disabled = True
            
            with self.output:
                print("Example saved successfully!")
    
    def add_example(self, content: str, scores: Dict[str, float], category: str, 
                   message_id: Optional[int] = None, notes: Optional[str] = None):
        """Add a new example."""
        example = SentimentExample(
            content=content,
            positive=scores['positive'],
            negative=scores['negative'],
            helpful=scores['helpful'],
            sarcastic=scores['sarcastic'],
            category=category,
            message_id=message_id,
            notes=notes
        )
        self.examples.append(example)
        self.save_examples()
    
    def generate_system_prompt(self) -> str:
        """Generate the complete system prompt with examples."""
        base_prompt = """Analyze the sentiment of the following message and return a JSON object with these scores:
- positive (0-1): How positive the message is
- negative (0-1): How negative the message is
- helpful (0-1): How helpful/constructive the message is
- sarcastic (0-1): How sarcastic the message is

Examples of different message types and their scores:"""

        categories = ['positive', 'negative', 'helpful', 'sarcastic']
        examples_text = []
        
        for category in categories:
            examples = [ex for ex in self.examples if ex.category == category]
            if examples:
                examples_text.append(f"\n{category.upper()} EXAMPLES:")
                for ex in examples[:3]:
                    examples_text.append(f"Message: {ex.content}")
                    examples_text.append(
                        f"Scores: positive={ex.positive}, negative={ex.negative}, "
                        f"helpful={ex.helpful}, sarcastic={ex.sarcastic}"
                    )
                    if ex.notes:
                        examples_text.append(f"Note: {ex.notes}")
        
        return f"{base_prompt}\n{''.join(examples_text)}\n\nOnly return the JSON object, nothing else."
    
    def display(self):
        """Display the main interface."""
        display(widgets.VBox([
            self.action_dropdown,
            self.output
        ]))