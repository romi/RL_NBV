#Running headless
 Pour lancer Blender sur une machine distante (sans display) , suivant cette réponse puis cette réponse.
D'abord il faut récupérer l'adresse du bus PCI de la cart graphique :
$ nvidia-xconfig --query-gpu-info
Number of GPUs: 2
GPU #0:
  Name      : GeForce GTX 1080 Ti
  UUID      : GPU-51fd343f-5147-2f34-1f52-b47893a7ac6e
  PCI BusID : PCI:59:0:0
  Number of Display Devices: 0
GPU #1:
  Name      : GeForce GTX 1080 Ti
  UUID      : GPU-854e79c3-546c-f891-f6b4-58e4d60e33a8
  PCI BusID : PCI:175:0:0
  Number of Display Devices: 0
Créer un fichier config pour X (ça devrait être fait qu'une seule fois) :
$ sudo nvidia-xconfig --busid=PCI:175:0:0 --use-display-device=none --virtual=1280x1024
Lancer X :
sudo Xorg :1
(C'est probalement mieux de créer un fichier de config à part plutôt que d'écraser la config X existante de la machine (à tester) :)
$ sudo nvidia-xconfig --busid=PCI:175:0:0 --use-display-device=none --virtual=1280x1024 -o my-xserver.conf
$ sudo Xorg :1 -config my-xserver.conf
Puis dans une autre console :
$ export DISPLAY=:1
$ blender -b -P script.py

https://devtalk.blender.org/t/blender-2-8-unable-to-open-a-display-by-the-rendering-on-the-background-eevee/1436/29
https://devtalk.blender.org/t/blender-2-8-unable-to-open-a-display-by-the-rendering-on-the-background-eevee/1436/24
