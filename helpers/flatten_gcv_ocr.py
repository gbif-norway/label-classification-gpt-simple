
import itertools

def is_close(block1, block2, distance=300):
    for point1, point2 in itertools.product(block1['vertices'], block2['vertices']):
        if abs(point1['x'] - point2['x']) <= distance and abs(point1['y'] - point2['y']) <= distance:
            return True
    return False

def merge_blocks(block1, block2):
    merged_vertices = [
        {"x": min(v["x"] for v in block1["vertices"] + block2["vertices"]), "y": min(v["y"] for v in block1["vertices"] + block2["vertices"])},
        {"x": max(v["x"] for v in block1["vertices"] + block2["vertices"]), "y": min(v["y"] for v in block1["vertices"] + block2["vertices"])},
        {"x": max(v["x"] for v in block1["vertices"] + block2["vertices"]), "y": max(v["y"] for v in block1["vertices"] + block2["vertices"])},
        {"x": min(v["x"] for v in block1["vertices"] + block2["vertices"]), "y": max(v["y"] for v in block1["vertices"] + block2["vertices"])}
    ]
    return {'vertices': merged_vertices, 'text': block1['text'] + ' ' + block2['text']}

def merge_close_blocks(blocks, distance=300):
    merged_blocks = []
    merged_indices = set()
    has_merged = False

    for i, block1 in enumerate(blocks):
        if i in merged_indices:
            continue

        new_block = block1.copy()
        for j, block2 in enumerate(blocks):
            if j in merged_indices or i == j:
                continue

            if is_close(new_block, block2, distance):
                new_block = merge_blocks(new_block, block2)
                merged_indices.add(j)
                has_merged = True

        merged_blocks.append(new_block)
        merged_indices.add(i)

    if has_merged:
        return merge_close_blocks(merged_blocks, distance)
    else:
        return merged_blocks

def flatten(document):
    blocks = []
    for page in document:
        for block in page['blocks']:
            ps = []
            for paragraph in block['paragraphs']:
                ws = []
                for word in paragraph['words']:
                    ws.append(''.join([l['text'] for l in word['symbols']]))
                ps.append(' '.join(ws))
            b = {
                'text': ' '.join(ps),
                'vertices': block['boundingBox']['vertices']
            }
            blocks.append(b)

    merged_blocks = merge_close_blocks(blocks)
    return '\n'.join([b['text'] for b in merged_blocks])
