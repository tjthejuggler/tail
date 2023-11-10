import json
import math
from diffusers import DiffusionPipeline
import torch
from torchvision.utils import save_image
from torchvision import transforms

# Initialize the pipeline
pipe = DiffusionPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    use_safetensors=True,
    variant="fp16"
)
pipe.to("cuda")

# Function to calculate the number of steps
def calculate_steps(item_number, max_items, min_steps=5, max_steps=50):
    # Scale the number of steps from min_steps to max_steps
    return min_steps + (max_steps - min_steps) * (item_number / max_items)

# Load prompts from the JSON file
with open('habits_wallpaper_prompts.txt', 'r') as file:
    prompts_dict = json.load(file)

# Sort the prompts by their keys (converted to integers)
sorted_prompts = sorted(prompts_dict.items(), key=lambda x: int(x[0]))

# Generate and save images with progressive quality
for prompt_number, prompt_text in sorted_prompts:
    num_steps = math.ceil(calculate_steps(int(prompt_number), len(sorted_prompts)))
    
    # Generate the image with the specified number of inference steps
    # Note: Adjust the 'num_inference_steps' parameter if available in your pipeline's generate function
    image = pipe(prompt=prompt_text).images[0]

    # Convert the PIL Image to a PyTorch tensor
    transform = transforms.ToTensor()
    tensor = transform(image)

    # Save the tensor to a file
    save_image(tensor, f'result_{prompt_number}.png')
