# Use Catholic

Site da loja Use Catholic: um único arquivo `index.html` (HTML, CSS e JavaScript juntos, com as imagens embutidas). Não precisa de build.

## Como publicar na Vercel

1. Na Vercel, clique em **Add New > Project** e escolha este repositório.
2. Em **Framework Preset**, deixe **Other**. Não preencha Build Command nem Output Directory.
3. Clique em **Deploy**.

Depois disso, cada alteração enviada para o branch `main` publica o site de novo, sozinha, em cerca de 1 minuto.

## Como adicionar um objeto 3D

No `index.html`, procure o trecho entre `OBJETOS3D_INICIO` e `OBJETOS3D_FIM` e acrescente um item na lista `OBJ`, com `sec`, `nome`, `fotos` e, se quiser, `desc` e `rotulos`. As seções são: `santos`, `maria`, `porta-tercos`, `sagrada-familia`, `simbolos` e `presentes`.

## Observações

- Pedidos saem pelo WhatsApp (83) 98720-0345.
- O login usa o Supabase (e-mail e senha). O endereço e a chave pública do projeto ficam no `index.html`, no trecho `SB_URL` e `SB_KEY`. Essa chave é pública de propósito. Nunca coloque ali a chave `secret` ou `service_role`.
- Cada pedido é guardado na tabela `orders` do Supabase, e só o próprio cliente enxerga os seus pedidos. Para criar a tabela, rode o arquivo `supabase-setup.sql` no SQL Editor do Supabase (ele não faz parte do site).
- Só quem tem conta consegue finalizar um pedido. Visitantes navegam por todo o site e montam a sacola normalmente; ao finalizar, o site pede para entrar ou criar a conta e depois leva de volta ao pedido, com a sacola guardada. Essa regra vale para o fluxo do site: o número de WhatsApp da loja continua aberto para dúvidas e conversas.
