# Pipeline de Dados com Apache HOP

Este projeto implementa pipelines de dados utilizando o Apache HOP para processar dados de currículos Lattes (plataforma brasileira de currículos de pesquisadores) e realizar buscas textuais em um banco de dados PostgreSQL.

## Descrição

O projeto extrai informações de arquivos XML do Lattes, armazena em PostgreSQL e configura uma busca textual avançada com suporte a pesos, buscas booleanas e sugestões de correção para erros de digitação.

## Funcionalidades

- **Extração de Dados**: Processamento de arquivos XML Lattes usando pipelines Apache HOP
- **Armazenamento**: Persistência em PostgreSQL com configurações otimizadas para português
- **Busca Textual**: Implementação de full-text search com pesos (A, B, C) para relevância
- **Buscas Avançadas**: Suporte a buscas simples e booleanas
- **Sugestões**: Correção automática de erros de digitação usando trigramas
- **Containerização**: Ambiente Docker para fácil execução
