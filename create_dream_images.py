#this script changes the KDE color theme based on how many habits I have done so far today

import os
import json
from diffusers import DiffusionPipeline
import torch
from torchvision.utils import save_image
from torchvision import transforms



with open('/home/lunkwill/projects/tail/obsidian_dir.txt', 'r') as f:
    obsidian_dir = f.read().strip()

def notify(text):
    print('text')    
    msg = "notify-send ' ' '"+text+"'"
    os.system(msg)

def create_image(sentence):
    pipe = DiffusionPipeline.from_pretrained("stabilityai/stable-diffusion-xl-base-1.0", torch_dtype=torch.float16, use_safetensors=True, variant="fp16")
    pipe.to("cuda")

    prompt = sentence

    image = pipe(prompt=prompt).images[0]

    # Convert the PIL Image to a PyTorch tensor
    transform = transforms.ToTensor()
    tensor = transform(image)

    filename = prompt.replace(' ', '_') + '.png'

    # Save the tensor to a file
    save_image(tensor, '/home/lunkwill/dream_generations/'+filename)

def main():
    submitted_dreams_file = obsidian_dir + 'submitted_dreams.txt'
    submitted_dreams_file = os.path.expanduser(submitted_dreams_file)
    with open(submitted_dreams_file, 'r') as f:
        submitted_dreams = f.read().strip()
    
    #remove %var from submitted_dreams
    submitted_dreams = submitted_dreams.replace('%note', '')

    final_submitted_dreams = submitted_dreams

    #split submitted_dreams into a list of sentences
    submitted_dreams = submitted_dreams.split('.')
  
    for sentence in submitted_dreams:
        create_image(sentence)
        final_submitted_dreams = final_submitted_dreams.replace(sentence, "")

    #write final_submitted_dreams to submitted_dreams_file
    with open(submitted_dreams_file, 'w') as f:
        f.write(final_submitted_dreams)


main()



