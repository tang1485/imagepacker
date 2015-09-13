#! /usr/bin/python
from PIL import Image, ImageDraw
import math
from pprint import pprint

# Based off of the great writeup, demo and code at:
# http://codeincomplete.com/posts/2011/5/7/bin_packing/

class Block():
    """A rectangular block, to be packed"""
    def __init__(self, w, h, data=None, padding=0):
        self.w = w
        self.h = h
        self.x = None
        self.y = None
        self.fit = None
        self.data = data
        self.padding = padding # not implemented yet

    def __str__(self):
        return "({x},{y}) ({w}x{h}): {data}".format(
            x=self.x,y=self.y, w=self.w,h=self.h, data=self.data)


class _BlockNode():
    """A BlockPacker node"""
    def __init__(self, x, y, w, h, used=False, right=None, down=None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.used = used
        self.right = right
        self.down = down

    def __repr__(self):
        return "({x},{y}) ({w}x{h})".format(x=self.x,y=self.y,w=self.w,h=self.h)


class BlockPacker():
    """Packs blocks of varying sizes into a single, larger block"""
    def __init__(self):
        self.root = None

    def fit(self, blocks):
        nblocks = len(blocks)
        w = blocks[0].w# if nblocks > 0 else 0
        h = blocks[0].h# if nblocks > 0 else 0

        self.root = _BlockNode(0,0, w,h)

        for block in blocks:
            node = self.find_node(self.root, block.w, block.h)
            if node:
                # print("split")
                node_fit = self.split_node(node, block.w, block.h)
                block.x = node_fit.x
                block.y = node_fit.y
            else:
                # print("grow")
                node_fit = self.grow_node(block.w, block.h)
                block.x = node_fit.x
                block.y = node_fit.y

    def find_node(self, root, w, h):
        if root.used:
            # raise Exception("used")
            node = self.find_node(root.right, w, h)
            if node:
                return node
            return self.find_node(root.down, w, h)
        elif w <= root.w and h <= root.h:
            return root
        else:
            return None

    def split_node(self, node, w, h):
        node.used = True
        node.down = _BlockNode(
            node.x, node.y + h,
            node.w, node.h - h
        )
        node.right = _BlockNode(
            node.x + w, node.y,
            node.w - w, h
        )
        return node

    def grow_node(self, w, h):
        can_grow_down = w <= self.root.w
        can_grow_right = h <= self.root.h

        # try to keep the packing square
        should_grow_right = can_grow_right and self.root.h >= (self.root.w + w)
        should_grow_down = can_grow_down and self.root.w >= (self.root.h + h)

        if should_grow_right:
            return self.grow_right(w, h)
        elif should_grow_down:
            return self.grow_down(w, h)
        elif can_grow_right:
            return self.grow_right(w, h)
        elif can_grow_down:
            return self.grow_down(w, h)
        else:
            raise Exception("no valid expansion avaliable!")

    def grow_right(self, w, h):
        old_root = self.root
        self.root = _BlockNode(
            0, 0,
            old_root.w + w, old_root.h,
            down=old_root,
            right=_BlockNode(self.root.w, 0, w, self.root.h),
            used=True
        )

        node = self.find_node(self.root, w, h)
        if node:
            return self.split_node(node, w, h)
        else:
            return None

    def grow_down(self, w, h):
        old_root = self.root
        self.root = _BlockNode(
            0, 0,
            old_root.w, old_root.h + h,
            down=_BlockNode(0, self.root.h, self.root.w, h),
            right=old_root,
            used=True
        )

        node = self.find_node(self.root, w, h)
        if node:
            return self.split_node(node, w, h)
        else:
            return None


def crop_by_extents(image, extent, wrap=False):
    image = image.convert("RGBA")
    # overlay = Image.new('RGBA', image.size, (255,255,255,0))

    w,h = image.size
    coords = [math.floor(extent.min_x*w), math.floor(extent.min_y*h),
              math.ceil(extent.max_x*w), math.ceil(extent.max_y*h)]
    print("\nEXTENT")
    pprint(extent)

    if min(extent.min_x,extent.min_y) < 0 or max(extent.max_x,extent.max_y) > 1:
        print("WARNING! UV Coordinates lying outside of [0:1] space!")

    pprint(coords)

    if extent.to_wrap:
        h_w, v_w = extent.wrapping()
        print("Ye", h_w, v_w)

        new_im = Image.new("RGBA", (math.ceil(h_w*w), math.ceil(v_w*h)))
        new_w, new_h = new_im.size

        # Iterate through a grid, to place the background tile
        for i in range(0, new_w, w):
            for j in range(0, new_h, h):
                #paste the image at location i, j:
                new_im.paste(image, (i, j))

        crop_coords = coords.copy()

        if crop_coords[0] < 0:
            crop_coords[2] = crop_coords[2] - crop_coords[0]
            crop_coords[0] = 0
        if crop_coords[1] < 0:
            crop_coords[3] = crop_coords[3] - crop_coords[1]
            crop_coords[1] = 0

        # crop_coords[0] = crop_coords[0]
        # crop_coords[1] = crop_coords[1]

        # crop_coords[2] = crop_coords[2]
        # crop_coords[3] = crop_coords[3]

        image = new_im.crop(crop_coords)

    else:
        coords[0] = max(coords[0], 0)
        coords[1] = max(coords[1], 0)

        coords[2] = min(coords[2], w)
        coords[3] = min(coords[3], h)

        image = image.crop(coords)

    changed_w = coords[2] - coords[0]
    changed_h = coords[3] - coords[1]

    # offset from origin x, y, horizontal scale, vertical scale
    changes = (coords[0], coords[1], changed_w/w, changed_h/h)
    pprint(changes)

    return (image, changes)

    # pprint(coords)

    # d = ImageDraw.Draw(overlay)
    # d.rectangle(coords, fill=(255,0,0,50))

    # return Image.alpha_composite(image, overlay)

def pack_images(image_paths, background=(0,0,0,0), format="PNG", extents=None, wrap=False):
    images = []
    blocks = []
    image_name_map = {}

    image_paths.sort() # sort so we get repeatable file ordering

    for filename in image_paths:
        print("opening", filename)
        image = Image.open(filename)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        # rescale images
        changes = None
        if extents:
            print(filename, image.size)
            image, changes = crop_by_extents(image, extents[filename], wrap=wrap)

        images.append(image)
        image_name_map[filename] = image

        w,h = image.size
        # using filename so we can pass back UV info without storing it in image
        blocks.append(Block(w,h, data=(filename, changes)))

    # sort by width, descending (widest first)
    blocks.sort(key=lambda block: -block.w)

    packer = BlockPacker()
    packer.fit(blocks)

    output_image = Image.new("RGBA", (packer.root.w, packer.root.h))

    uv_changes = {}
    for block in blocks:
        # print(block)
        fname, changes = block.data
        image = image_name_map[fname]
        uv_changes[fname] = {
            "offset": (
                # should be in [0, 1] range
                (block.x - changes[0])/output_image.size[0],
                # UV origin is bottom left, PIL assumes top left!
                # 1 - (block.y + image.size[1])/output_image.size[1]
                (block.y - changes[1])/output_image.size[1]
            ),

            "aspect": (
                (1/changes[2])* (image.size[0]/output_image.size[0]),
                (1/changes[3])* (image.size[1]/output_image.size[1])
            ),


            # "global": {
            #     "aspect": (
            #         (image.size[0]/output_image.size[0]),
            #         (image.size[1]/output_image.size[1])
            #     ),

            #     "offset": (
            #         # should be in [0, 1] range
            #         (block.x/output_image.size[0],
            #         # UV origin is bottom left, PIL assumes top left!
            #         # 1 - (block.y + image.size[1])/output_image.size[1]
            #         (block.x - changes[1])/output_image.size[1]
            #     )
            # }
        }

        output_image.paste(image, (block.x, block.y))

    output_image = output_image.transpose(Image.FLIP_TOP_BOTTOM)
    return output_image, uv_changes

if __name__ == '__main__':
    import glob
    from pprint import pprint
    filenames = glob.glob("E:\Applications\BTSync\Home Share\Programming\SimpleModelPacker\*.tga")
    print(filenames)
    if len(filenames) > 0:
        img,uv = pack_images(filenames)
        img.show()
        pprint(uv)