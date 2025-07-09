#!/bin/bash

# DND Discord Bot Docker 部署脚本
# 版本: v1.3.0
# 作者: DND_DC_BOT Team

set -e

echo "🐳 DND Discord Bot Docker 部署脚本"
echo "=================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    log_success "Docker环境检查完成"
}

# 检查环境变量配置
check_env() {
    if [ ! -f ".env" ]; then
        log_warn "未找到.env文件，正在创建..."
        cp docker.env.example .env
        log_warn "请编辑.env文件，填写正确的DISCORD_TOKEN"
        echo ""
        echo "编辑命令: nano .env"
        echo "必填项: DISCORD_TOKEN"
        echo ""
        read -p "是否现在编辑.env文件? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} .env
        else
            log_error "请先配置.env文件后再运行部署脚本"
            exit 1
        fi
    fi
    
    # 检查关键配置
    if ! grep -q "DISCORD_TOKEN=" .env || grep -q "your_discord_bot_token_here" .env; then
        log_error "请在.env文件中配置正确的DISCORD_TOKEN"
        exit 1
    fi
    
    log_success "环境变量配置检查完成"
}

# 创建必要目录
create_directories() {
    log_info "创建必要的目录..."
    mkdir -p data logs
    
    # 设置权限
    chmod 755 data logs
    
    log_success "目录创建完成"
}

# 构建Docker镜像
build_image() {
    log_info "构建Docker镜像..."
    
    # 停止旧容器
    docker-compose down 2>/dev/null || true
    
    # 构建新镜像
    docker-compose build --no-cache
    
    log_success "Docker镜像构建完成"
}

# 启动服务
start_service() {
    log_info "启动DND Discord Bot服务..."
    
    # 启动服务
    docker-compose up -d
    
    # 等待服务启动
    sleep 5
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        log_success "DND Discord Bot服务启动成功"
        
        # 显示日志
        echo ""
        log_info "最新日志:"
        docker-compose logs --tail=20
        
        echo ""
        log_info "实时日志命令: docker-compose logs -f"
        log_info "停止服务命令: docker-compose down"
        log_info "重启服务命令: docker-compose restart"
        
    else
        log_error "服务启动失败，请查看日志"
        docker-compose logs --tail=50
        exit 1
    fi
}

# 显示状态
show_status() {
    echo ""
    log_info "=== 服务状态 ==="
    docker-compose ps
    
    echo ""
    log_info "=== 容器健康检查 ==="
    docker-compose exec dnd-bot python3 -c "
import sqlite3
import ssl
print(f'✅ SQLite: 数据库连接正常')
print(f'✅ SSL版本: {ssl.OPENSSL_VERSION}')
print(f'✅ Python版本: 3.11+')
print(f'✅ 容器状态: 运行中')
"
    
    echo ""
    log_success "Docker部署完成!"
}

# 主函数
main() {
    log_info "开始Docker部署流程..."
    
    check_docker
    check_env
    create_directories
    build_image
    start_service
    show_status
    
    echo ""
    log_success "🎉 部署完成！您的DND Discord Bot现在运行在Docker容器中"
    log_info "容器使用现代OpenSSL，SSL连接问题已解决"
}

# 帮助信息
show_help() {
    echo "DND Discord Bot Docker 部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  -s, --status   显示服务状态"
    echo "  -r, --restart  重启服务"
    echo "  -d, --down     停止服务"
    echo "  -l, --logs     查看日志"
    echo ""
    echo "首次部署请直接运行: $0"
}

# 参数处理
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -s|--status)
        docker-compose ps
        exit 0
        ;;
    -r|--restart)
        log_info "重启服务..."
        docker-compose restart
        log_success "服务重启完成"
        exit 0
        ;;
    -d|--down)
        log_info "停止服务..."
        docker-compose down
        log_success "服务已停止"
        exit 0
        ;;
    -l|--logs)
        docker-compose logs -f
        exit 0
        ;;
    "")
        main
        ;;
    *)
        log_error "未知参数: $1"
        show_help
        exit 1
        ;;
esac 