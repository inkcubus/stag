#!/usr/bin/env python3

#############################################
## STAG                                     #
## Stephan's Automatic Image Tagger         #
#############################################

import argparse
import threading

import rawpy
import torch

from huggingface_hub import hf_hub_download
from PIL import Image
from ram import get_transform
from ram import inference_ram as inference
from ram.models import ram_plus
from xmphandler import *
from pillow_heif import register_heif_opener


class SKTagger:

    def __init__(self, model_path, image_size,
                 a_force, a_test, a_prefer_exact, a_prefix ):
        register_heif_opener()
        self.transform = get_transform(image_size=image_size)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print("STAG using device ", self.device)
        self.model = ram_plus(pretrained=model_path, image_size=image_size, vit='swin_l')
        self.model.eval()
        self.model = self.model.to(self.device)
        self.a_force = a_force
        self.a_test = a_test
        self.a_prefer_exact = a_prefer_exact
        self.a_prefix = a_prefix


    def get_tags_for_image(self, pil_image):
        try:
            torch_image = self.transform(pil_image).unsqueeze(0).to(self.device)
            res=inference(torch_image, self.model)
            return res[0]
        except Exception as e:
            print ("Tagging failed: ",str(e))
            return ""

    def get_tags_for_image_at_path(self, path):
        pillow_image = Image.open(path)
        return self.get_tags_for_image(pillow_image)

    def enter_dir(self, img_dir, stop_event):
        print("Entering " + img_dir)
        for current_dir, subdirList, fileList in os.walk(img_dir):
            for fname in sorted(fileList):

                if stop_event.is_set():
                    print("Tagging cancelled.")
                    return

                if fname.startswith("."):
                    # nothing but trouble with hidden files, so skip those
                    continue

                image_file = os.path.join(current_dir, fname)
                image = None
                filename, file_extension = os.path.splitext(image_file)
                file_extension = file_extension.lower()
                sidecar_files = XMPHandler.get_xmp_sidecars_for_image(image_file)

                # determine if we already have tagged this image
                already_tagged = False
                if not self.a_force:
                    for current_file in sidecar_files:
                        handler= XMPHandler(current_file)
                        already_tagged |= handler.has_subject_prefix(self.a_prefix)

                if not already_tagged:
                    if file_extension in [".jpg", ".jpeg", ".tiff", ".tif", ".png", ".heic"]:
                        try:
                            image = Image.open(image_file)
                        except Exception as e:
                            print ("could not read", image_file, e)
                    elif file_extension != ".xmp":
                        # not one of the known file types and not xmp? Could be a raw file.
                        try:
                            with rawpy.imread(image_file) as raw:
                                rgb = raw.postprocess()
                                image = Image.fromarray(rgb)
                        except Exception as e:
                            print("Could not read ", image_file, " because of ", str(e))

                    if image is not None:
                        print('Looking at %s:' % image_file)
                        res = [item.strip() for item in self.get_tags_for_image(image).split("|")]
                        print("Tags found: ", res)
                        if res != "":
                            if len(sidecar_files) == 0:
                                if self.a_test is not True:
                                    sidecar_files = [XMPHandler.create_xmp_sidecar(image_file, self.a_prefer_exact)]
                                else:
                                    print("skipping XMP file creation, not writing tags")
                            for current_file in sidecar_files:
                                handler = XMPHandler(current_file)
                                for t in res:
                                    handler.add_hierarchical_subject(self.a_prefix+"|"+t)
                                if self.a_test is not True:
                                    handler.save()
                else:
                    if file_extension != ".xmp":
                        print("File %s already tagged." % fname)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='STAG image tagger')

    parser.add_argument('imagedir',
                        metavar='DIR',
                        help='path to dataset')

    parser.add_argument('--prefix',
                        metavar='STR',
                        help='top category for tags (default="st")',
                        default='st')

    parser.add_argument('--force',
                        action='store_true',
                        help='force tagging, even if images are already tagged')

    parser.add_argument('--test',
                        action='store_true',
                        help="don't actually write or modify XMP files")

    parser.add_argument('--prefer-exact-filenames',
                        action='store_true',
                        help="write <originial_file_name>.<original_file_extension>.xmp instead of <original_file_name>.xmp")

    args = parser.parse_args()
    pretrained = hf_hub_download(repo_id="xinyu1205/recognize-anything-plus-model",
                                 filename="ram_plus_swin_large_14m.pth")

    tagger = SKTagger(pretrained, 384, args.force, args.test, args.prefer_exact_filenames, args.prefix)
    stop_event = threading.Event()
    stop_event.clear()
    tagger.enter_dir(args.imagedir, stop_event)


