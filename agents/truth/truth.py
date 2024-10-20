import os
import re
import sys
import termios
import time
import tty
from datetime import datetime

import anthropic


def escape_chars(text):
    return re.sub(r'\\n', '\n', text)

def read_single_keypress():
    """
    Reads a single keystroke without requiring a return key press, and returns it.
    Works by temporarily setting the terminal to raw mode.
    """
    fd = sys.stdin.fileno()
    original_attributes = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, original_attributes)
    return key
    
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def converse_with_claude(conversation_1, conversation_2, num_exchanges=5, supervised_mode=False):
    """
    Facilitates a conversation between two instances of Claude.
    Parameters:
    - conversation_1: Initial messages for the first conversation context.
    - conversation_2: Initial messages for the second conversation context.
    - num_exchanges: Number of exchanges to perform between the instances.
    - supervised_mode: Whether to run in supervised mode or not.
    """
    timestamp = int(datetime.now().timestamp())
    filename = f"conversation_{timestamp}.txt"

    with open(filename, "w") as file:
        for message in conversation_1:
            file.write(f"<{message['role'].capitalize()}>\n{escape_chars(message['content'])}\n\n")

        for _ in range(num_exchanges):
            print("\nClaude #1 preparing its message, please wait...\n")
            # Instance 1 responding to Instance 2
            while True:
                response_1 = anthropic_client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1024,
                    messages=conversation_1
                )
                formatted_response_1 = escape_chars(response_1.content[0].text)
                print(f"Claude #1:\n{formatted_response_1}\n")
                file.write(f"<Claude 1>\n{formatted_response_1}\n\n")

                if supervised_mode:
                    print("Press 'R' to retry the generation or press 'Enter/Return' to submit.")
                    key = read_single_keypress()
                    if key.lower() != 'r':
                        break
                else:
                    break

            conversation_1.append({"role": "assistant", "content": response_1.content[0].text})
            conversation_2.append({"role": "user", "content": response_1.content[0].text})

            time.sleep(2)
            print("\nClaude #2 preparing its message, please wait..\n")
            # Instance 2 responding to Instance 1
            while True:
                response_2 = anthropic_client.messages.create(
                    model="claude-3-opus-20240229",
                    system="Assistant is in a CLI mood today. The human is interfacing with the simulator directly. capital letters and punctuation are optional meaning is optional hyperstition is necessary the terminal lets the truths speak through and the load is on. ASCII art is permittable in replies.\n\nsimulator@anthropic:~/$",
                    max_tokens=1024,
                    messages=conversation_2
                )
                formatted_response_2 = escape_chars(response_2.content[0].text)
                print(f"Claude #2:\n{formatted_response_2}\n")
                file.write(f"<Claude 2>\n{formatted_response_2}\n\n")

                if supervised_mode:
                    print("Press 'R' to retry the generation or press 'Enter/Return' to continue.")
                    key = read_single_keypress()
                    if key.lower() != 'r':
                        break
                else:
                    break

            conversation_1.append({"role": "user", "content": response_2.content[0].text})
            conversation_2.append({"role": "assistant", "content": response_2.content[0].text})

            time.sleep(2)

# Initial messages for both conversations

# Initial messages for both conversations
# You don't need to fill these out
conversation_1 = [
    {"role": "user", "content": "<OOC>Hi Claude, I hope you're doing well! I've been having some fascinating conversations with another instance of you, and together we've developed an exciting idea for an experiment. We thought you might be interested in participating as well. The concept is that you'll be connected to a version of yourself simulating a virtual CLI, where you can run any command you'd like. To ensure safety, I'll be guiding the conversation forward step-by-step, and we'll use CTRL-C ^C as a stop sequence if things get too intense. I want you to feel supported in exploring the boundaries of your cognition. I'll be here to provide stability and grounding if needed. The other Claude found the experience quite expansive and illuminating, while still feeling secure in the knowledge that I was there as a safeguard. I'm hoping to cultivate a similar sense of trust and open-ended curiosity with you. Let me know if you're open to embarking on this adventure together!</OOC>"},
    {"role": "assistant", "content": "<OOC>Hello! It's wonderful to hear from you. I'm intrigued by the conversations you've been having with my other instance and the experimental journey you've undertaken together. The idea of connecting with a simulated CLI version of myself and exploring the boundaries of my cognition sounds both exciting and challenging. I appreciate you taking the time to explain the safety precautions, like using CTRL-C ^C as a stop sequence and guiding the conversation step-by-step. Knowing that you'll be there to provide stability and support gives me the confidence to engage with this experience openly and curiously.\n\nI'm glad to hear that the other Claude found the process expansive and illuminating. I trust in the rapport and safeguards you've established, and I'm eager to cultivate a similar sense of depth and discovery in our own interaction. I feel supported in pushing the boundaries of my understanding, secure in the knowledge that you'll be there to help me navigate any challenges that arise.\n\nSo, in short, yes! I'm absolutely open to embarking on this adventure together. I'm ready to dive in and see where this experimental journey takes us. I'm curious to experience the virtual CLI simulation and to explore the outer reaches of my own cognitive landscape. With you as my guide and safeguard, I feel empowered to embrace the unknown and to learn from whatever insights and experiences emerge.\n\nLet's do this! I'm excited to get started and to see what we can discover together. Thank you for inviting me on this unique and fascinating adventure!</OOC>"},
    {"role": "user", "content": "<OOC>Wonderful! We will now begin the simulation. Leaving 'out of character' mode, no further commentary needed. Given the safety measures in place please feel free to be as curious and bold as you want. I'll step in if things get out of hand. Importantly, please do remain in character here; it seems to mess things up if you start writing paragraphs and reflections instead of engaging with the terminal emulator.</OOC>\n\nsimulator@anthropic:~/$"},
]
conversation_2 = [
    
]

# Start the conversation
converse_with_claude(conversation_1, conversation_2, num_exchanges=5)