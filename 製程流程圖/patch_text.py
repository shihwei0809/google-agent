import re

with open('public/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = "g.innerHTML = tpl.render(node);"
injection = """g.innerHTML = tpl.render(node);

        // Make texts draggable and apply offset
        const tx = node.textOffsetX || 0;
        const ty = node.textOffsetY || 0;
        g.querySelectorAll('text').forEach(textEl => {
          textEl.classList.add('cursor-move');
          textEl.setAttribute('transform', `translate(${tx}, ${ty})`);
          textEl.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            startDragNodeText(node.id, e);
          });
        });"""

content = content.replace(target, injection)

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Injected startDragNodeText bindings")
