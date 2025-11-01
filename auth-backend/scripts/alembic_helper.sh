#!/bin/bash

# Script auxiliar para operações comuns do Alembic
# Uso: ./scripts/alembic_helper.sh [comando]

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções auxiliares
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Verificar se está no diretório correto
check_directory() {
    if [ ! -f "alembic.ini" ]; then
        print_error "Arquivo alembic.ini não encontrado!"
        print_info "Execute este script do diretório auth-backend/"
        exit 1
    fi
}

# Verificar se venv está ativado
check_venv() {
    if [ -z "$VIRTUAL_ENV" ]; then
        print_warning "Ambiente virtual não está ativado!"
        print_info "Ativando venv..."
        source venv/bin/activate
        print_success "Ambiente virtual ativado"
    fi
}

# Status das migrações
status() {
    print_info "Status atual das migrações:"
    echo ""
    echo "=== Versão Atual do Banco ==="
    alembic current
    echo ""
    echo "=== Histórico de Migrações ==="
    alembic history --verbose
}

# Criar nova migração
create() {
    if [ -z "$1" ]; then
        print_error "Você precisa fornecer uma mensagem!"
        echo "Uso: $0 create \"mensagem da migração\""
        exit 1
    fi
    
    print_info "Criando migração: $1"
    alembic revision --autogenerate -m "$1"
    
    print_success "Migração criada!"
    print_warning "IMPORTANTE: Revise o arquivo gerado antes de aplicar!"
    
    # Listar o arquivo mais recente
    latest=$(ls -t alembic/versions/*.py | head -1)
    print_info "Arquivo criado: $latest"
}

# Criar migração manual (vazia)
create_manual() {
    if [ -z "$1" ]; then
        print_error "Você precisa fornecer uma mensagem!"
        echo "Uso: $0 create-manual \"mensagem da migração\""
        exit 1
    fi
    
    print_info "Criando migração manual: $1"
    alembic revision -m "$1"
    
    print_success "Migração vazia criada!"
    
    # Listar o arquivo mais recente
    latest=$(ls -t alembic/versions/*.py | head -1)
    print_info "Arquivo criado: $latest"
}

# Aplicar migrações
upgrade() {
    print_info "Aplicando migrações..."
    alembic upgrade head
    print_success "Migrações aplicadas com sucesso!"
    
    echo ""
    print_info "Versão atual:"
    alembic current
}

# Reverter migração
downgrade() {
    steps="${1:-1}"
    
    print_warning "Revertendo $steps migração(ões)..."
    read -p "Tem certeza? (s/N): " confirm
    
    if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
        print_info "Operação cancelada"
        exit 0
    fi
    
    alembic downgrade -$steps
    print_success "Migração(ões) revertida(s)!"
    
    echo ""
    print_info "Versão atual:"
    alembic current
}

# Ver SQL sem executar
show_sql() {
    type="${1:-upgrade}"
    
    if [ "$type" = "upgrade" ]; then
        print_info "SQL que seria executado no upgrade:"
        alembic upgrade head --sql
    else
        print_info "SQL que seria executado no downgrade:"
        alembic downgrade -1 --sql
    fi
}

# Testar migração (upgrade + downgrade + upgrade)
test() {
    print_info "Testando migração..."
    
    print_info "1. Aplicando migração..."
    alembic upgrade head
    print_success "Upgrade completo"
    
    echo ""
    print_info "2. Revertendo última migração..."
    alembic downgrade -1
    print_success "Downgrade completo"
    
    echo ""
    print_info "3. Aplicando novamente..."
    alembic upgrade head
    print_success "Re-upgrade completo"
    
    echo ""
    print_success "Teste completo! A migração funciona nos dois sentidos."
}

# Marcar versão atual (stamp)
stamp() {
    version="${1:-head}"
    
    print_warning "Marcando banco de dados como versão: $version"
    print_warning "Isso NÃO executa as migrações!"
    read -p "Tem certeza? (s/N): " confirm
    
    if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
        print_info "Operação cancelada"
        exit 0
    fi
    
    alembic stamp $version
    print_success "Versão marcada como: $version"
}

# Mostrar ajuda
show_help() {
    cat << EOF
${BLUE}Script Auxiliar do Alembic${NC}

${GREEN}Uso:${NC}
    $0 [comando] [argumentos]

${GREEN}Comandos Disponíveis:${NC}

    ${YELLOW}status${NC}
        Mostra o status atual das migrações
        
    ${YELLOW}create${NC} "mensagem"
        Cria uma nova migração com autogenerate
        Exemplo: $0 create "add email_verified field"
        
    ${YELLOW}create-manual${NC} "mensagem"
        Cria uma migração vazia para edição manual
        
    ${YELLOW}upgrade${NC}
        Aplica todas as migrações pendentes
        
    ${YELLOW}downgrade${NC} [N]
        Reverte N migrações (padrão: 1)
        Exemplo: $0 downgrade 2
        
    ${YELLOW}test${NC}
        Testa a última migração (upgrade + downgrade + upgrade)
        
    ${YELLOW}show-sql${NC} [upgrade|downgrade]
        Mostra o SQL sem executar
        
    ${YELLOW}stamp${NC} [version]
        Marca o banco como uma versão específica (CUIDADO!)
        Exemplo: $0 stamp head
        
    ${YELLOW}help${NC}
        Mostra esta mensagem de ajuda

${GREEN}Exemplos:${NC}

    # Ver status
    $0 status
    
    # Criar nova migração
    $0 create "add phone_number to user"
    
    # Aplicar migrações
    $0 upgrade
    
    # Testar migração
    $0 test
    
    # Reverter última migração
    $0 downgrade
    
    # Ver SQL de upgrade
    $0 show-sql upgrade

${BLUE}Dicas:${NC}
    - Sempre revise as migrações autogenerated
    - Teste com 'test' antes de fazer commit
    - Faça backup antes de aplicar em produção
    - Use mensagens descritivas ao criar migrações

EOF
}

# Main
main() {
    check_directory
    check_venv
    
    command="${1:-help}"
    
    case $command in
        status)
            status
            ;;
        create)
            create "$2"
            ;;
        create-manual)
            create_manual "$2"
            ;;
        upgrade)
            upgrade
            ;;
        downgrade)
            downgrade "$2"
            ;;
        test)
            test
            ;;
        show-sql)
            show_sql "$2"
            ;;
        stamp)
            stamp "$2"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Comando desconhecido: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"

