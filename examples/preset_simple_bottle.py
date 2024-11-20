from rich import print

from prompt_bottle import pb_img_url, simple_bottle

temp = simple_bottle(
    system="You are a helpful assistant {{ picture }}",
    user="What is the capital of {{ country }}? And what is the city in the picture? {{ picture }}",
)

print(
    temp.render(country="France", picture=pb_img_url("https://example.com/image.jpg"))
)
