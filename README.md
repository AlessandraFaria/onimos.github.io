# onimos — site

Página estática de apresentação do [onimos](https://github.com/), feita pra ser hospedada direto no GitHub Pages. Sem framework, sem build step — HTML, CSS e um JS pequeno pro widget interativo do hero.

## Publicar no GitHub Pages

1. Suba o conteúdo desta pasta pra raiz de um repositório (ou pra uma branch `gh-pages`, ou pra uma pasta `docs/` na branch principal — as três formas funcionam).
2. No repositório, vá em **Settings → Pages**.
3. Em **Source**, escolha a branch e a pasta onde este conteúdo está (`/ (root)` ou `/docs`).
4. Salva. O GitHub publica em `https://<seu-usuario>.github.io/<repositorio>/` em alguns minutos.

O arquivo `.nojekyll` já está incluso, pra desativar o processamento Jekyll padrão do GitHub Pages — não precisa dele pra um site estático simples como esse, e evita comportamento inesperado com nomes de arquivo que começam com `_`.

## Rodar localmente

Qualquer servidor estático serve:

```bash
python3 -m http.server 8000
```

Depois abre `http://localhost:8000`.

## Estrutura

```
index.html      conteúdo e estrutura da página
styles.css      tema visual (tokens de cor, tipografia, layout)
script.js       widget interativo do hero (troca de contexto ao vivo)
assets/
  logo.png            logo com fundo transparente, usado no site
  logo-original.png   arquivo original enviado, com fundo branco
```

## Ajustar conteúdo

Os exemplos de código na seção de instalação e os textos de definição do widget do hero foram tirados do comportamento real do projeto — se a API do pacote mudar, vale conferir se os trechos em `index.html` (seção `#instalacao`) e `script.js` (objeto `DEFINITIONS`) ainda batem com o código atual.
