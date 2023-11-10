from diffusers import StableDiffusionPipeline

# Load the model
pipe = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4", use_auth_token=True)

# Move the pipeline to the GPU if available
pipe = pipe.to("cuda")

# Generate an image from a text prompt
prompt = "a fantasy landscape with mountains and a river, digital art"
image = pipe(prompt)["sample"][0]

# Save the image
image.save("generated_image.png")
