
from core.storyteller import StoryTeller
import sys

def test_storyteller():
    try:
        teller = StoryTeller(model_name="ai-forever/rugpt3small_based_on_gpt2", device="cpu")
        
        # Test Case 1: Educational Mode - Bubble Sort
        print("\n--- Test Case 1: Educational Mode (Bubble Sort) ---")
        topic = "Алгоритм сортировки пузырьком"
        style = "Educational"
        intro_prompt = f"Тема занятия: {topic}. Стиль изложения: {style}. Введение:"
        
        response = teller.generate_response("Лекция началась.", intro_prompt, educational_mode=True)
        print(f"Prompt: {intro_prompt}")
        print(f"Response: {response}")
        
        if "игр" in response.lower() and "психолог" in response.lower():
            print("FAILURE: Response still contains game/psychology hallucinations.")
        else:
            print("SUCCESS: Response seems relevant (or at least not the specific game hallucination).")

        # Test Case 2: Story Mode - Bubble Sort (Control Group)
        print("\n--- Test Case 2: Story Mode (Control) ---")
        intro_prompt_story = f"История начинается. Главный герой: {topic}. Жанр: {style}. Начало:"
        response_story = teller.generate_response("Вступление:", intro_prompt_story, educational_mode=False)
        print(f"Prompt: {intro_prompt_story}")
        print(f"Response: {response_story}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_storyteller()
