import torch
from torchvision import transforms
from modelos.U_Net.model import UNetResnet
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
model = UNetResnet()
pesos=r'modelos\U_Net\path_modelo_entrenado1.pth'
device = "cuda" if torch.cuda.is_available() else "cpu"

# Transformaciones para preprocesar la imagen
transform = transforms.Compose([
    transforms.Resize((416, 512)),  # Ajusta al tamaño esperado por tu modelo
    transforms.ToTensor(),
])



def apply_colormap(image, cmap_name='jet'):
    cmap = plt.get_cmap(cmap_name)
    colored_image = cmap(image)
    return colored_image


def evaluar(imagen_path):
    model.load_state_dict(torch.load(pesos))
    model.eval()
    imagen = Image.open(imagen_path).convert('RGB')
    image = transform(imagen).unsqueeze(0)
    with torch.no_grad():
        output = model(image)
        pred_mask = torch.argmax(output, 0)
    imagen_resultado = transforms.ToPILImage()(output.squeeze().cpu().numpy())
    imagen_coloreada = apply_colormap(np.array(imagen_resultado)) 

    # Normalizar a [0, 1] y luego escalar a [0, 255]
    imagen_coloreada = (imagen_coloreada - np.min(imagen_coloreada)) / (np.max(imagen_coloreada) - np.min(imagen_coloreada)) * 255

    #       Convertir a uint8 antes de guardar
    imagen_coloreada = Image.fromarray(imagen_coloreada.astype(np.uint8))
    imagen_coloreada = imagen_coloreada.convert('RGB')
    return imagen_coloreada