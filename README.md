# Use Catholic · site

Loja online de camisas católicas e objetos 3D. Site estático na Vercel (deploy automático a cada push no `main`).

## Como o site é montado

- `fonte/index.html` é o app (HTML, CSS e JavaScript num arquivo só). **Toda mudança no site é feita aqui.**
- `fonte/site.json` guarda as configurações: endereço oficial, ID do Google Analytics (`ga_id`), código do Search Console (`gsc`), telefone, Instagram e cidade.
- `python3 ferramentas/build.py` gera, a partir da fonte, tudo o que vai para o ar:
  - uma página pronta por endereço: `/`, `/camisas`, `/camisas/<estampa>`, `/objetos-3d/<seção>`, `/objetos-3d/<seção>/<peça>`, `/lancamentos`, `/quem-somos`, `/duvidas` e `/privacidade`;
  - em cada página: título igual ao h1, descrição, endereço oficial (canonical), prévia para WhatsApp e Instagram (Open Graph), dados para o Google (JSON-LD: loja, produtos com preço, migalhas, perguntas frequentes) e os produtos já escritos no HTML;
  - `sitemap.xml`, `robots.txt` e `llms.txt` (resumo da loja para assistentes de IA);
  - as páginas internas da loja (`/sacola`, `/finalizar`, `/conta`…) com `noindex`.
- Fotos: camisas em `img/camisas/` (webp de 720 px e 400 px), objetos 3D em `objetos/`, prévia geral em `img/og.jpg`.
- Os links antigos com `#` (`#camisas`, `#camisa-sao-bento`, `#obj-santos`…) continuam funcionando e levam ao endereço novo.

## Novos objetos 3D

`python3 /home/claude/catalogo-3d/add_objetos.py` publica as fotos de `catalogo-3d/fotos/` na fonte e roda o build sozinho.

## Medição (Google Analytics 4)

Com `ga_id` preenchido em `fonte/site.json` e o build rodado, o site passa a medir visitas e toques no WhatsApp (evento `whatsapp_click`), com aviso de cookies (LGPD) e modo de consentimento: sem autorização, nenhum cookie é gravado. A política de privacidade muda de texto sozinha.

## Testes locais

```
python3 ferramentas/serve.py . 8792          # servidor parecido com a Vercel
python3 ferramentas/medir.py http://127.0.0.1:8792/   # tempo no celular em 4G lento
```
