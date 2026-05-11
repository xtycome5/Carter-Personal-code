#!/bin/bash
# ============================================================
# Dream Recorder - 阿里云资源开设脚本
# 
# 使用前请先配置 AKSK：
#   export ALIBABA_CLOUD_ACCESS_KEY_ID=your-access-key-id
#   export ALIBABA_CLOUD_ACCESS_KEY_SECRET=your-access-key-secret
#
# 或者直接运行: aliyun configure
# ============================================================

set -e

# ============ 配置区域 ============
REGION="ap-southeast-1"           # 新加坡（国际站推荐）
ZONE="${REGION}a"                  # 可用区
PROJECT_NAME="dreamrecorder"
ECS_INSTANCE_TYPE="ecs.t6-c1m2.large"  # 2核4G（测试够用）
ECS_IMAGE="ubuntu_22_04_x64_20G_alibase_20240101.vhd"
ECS_DISK_SIZE=40                  # 系统盘 40GB
ECS_PASSWORD=""                   # 将在运行时提示输入

# ============ 颜色输出 ============
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ============ 检查前置条件 ============
check_prerequisites() {
    info "检查前置条件..."
    
    if ! command -v aliyun &> /dev/null; then
        error "未安装 aliyun CLI，请先安装: brew install aliyun-cli"
    fi
    
    # 验证认证
    aliyun ecs DescribeRegions --output cols=RegionId rows=Regions.Region[] 2>/dev/null || \
        error "AKSK 认证失败，请运行: aliyun configure"
    
    info "认证通过 ✓"
}

# ============ 创建 VPC ============
create_vpc() {
    info "创建 VPC..."
    
    VPC_ID=$(aliyun vpc CreateVpc \
        --RegionId $REGION \
        --VpcName "${PROJECT_NAME}-vpc" \
        --CidrBlock "172.16.0.0/16" \
        --Description "Dream Recorder VPC" \
        2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin)['VpcId'])")
    
    info "VPC 创建成功: $VPC_ID"
    sleep 5
    
    # 创建交换机
    VSWITCH_ID=$(aliyun vpc CreateVSwitch \
        --RegionId $REGION \
        --ZoneId $ZONE \
        --VpcId $VPC_ID \
        --VSwitchName "${PROJECT_NAME}-vsw" \
        --CidrBlock "172.16.1.0/24" \
        2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin)['VSwitchId'])")
    
    info "VSwitch 创建成功: $VSWITCH_ID"
}

# ============ 创建安全组 ============
create_security_group() {
    info "创建安全组..."
    
    SG_ID=$(aliyun ecs CreateSecurityGroup \
        --RegionId $REGION \
        --VpcId $VPC_ID \
        --SecurityGroupName "${PROJECT_NAME}-sg" \
        --Description "Dream Recorder Security Group" \
        2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin)['SecurityGroupId'])")
    
    # 开放端口
    for PORT in 22 80 443 3000 8000; do
        aliyun ecs AuthorizeSecurityGroup \
            --RegionId $REGION \
            --SecurityGroupId $SG_ID \
            --IpProtocol tcp \
            --PortRange "${PORT}/${PORT}" \
            --SourceCidrIp "0.0.0.0/0" \
            --Policy accept 2>/dev/null
    done
    
    info "安全组创建成功: $SG_ID (开放 22/80/443/3000/8000)"
}

# ============ 创建 ECS 实例 ============
create_ecs() {
    info "创建 ECS 实例 (${ECS_INSTANCE_TYPE})..."
    
    if [ -z "$ECS_PASSWORD" ]; then
        read -sp "请输入 ECS 登录密码(8-30位，含大小写+数字): " ECS_PASSWORD
        echo
    fi
    
    INSTANCE_ID=$(aliyun ecs CreateInstance \
        --RegionId $REGION \
        --ZoneId $ZONE \
        --InstanceType $ECS_INSTANCE_TYPE \
        --ImageId $ECS_IMAGE \
        --VSwitchId $VSWITCH_ID \
        --SecurityGroupId $SG_ID \
        --InstanceName "${PROJECT_NAME}-server" \
        --HostName "dreamrecorder" \
        --InternetChargeType "PayByTraffic" \
        --InternetMaxBandwidthOut 10 \
        --SystemDisk.Category "cloud_essd" \
        --SystemDisk.Size $ECS_DISK_SIZE \
        --InstanceChargeType "PostPaid" \
        --Password "$ECS_PASSWORD" \
        2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin)['InstanceId'])")
    
    info "ECS 实例创建成功: $INSTANCE_ID"
    
    # 分配公网 IP
    aliyun ecs AllocatePublicIpAddress --InstanceId $INSTANCE_ID 2>/dev/null
    
    # 启动实例
    aliyun ecs StartInstance --InstanceId $INSTANCE_ID 2>/dev/null
    info "ECS 正在启动..."
    sleep 30
    
    # 获取公网 IP
    PUBLIC_IP=$(aliyun ecs DescribeInstances \
        --RegionId $REGION \
        --InstanceIds "[\"$INSTANCE_ID\"]" \
        2>/dev/null | python3 -c "
import sys,json
data=json.load(sys.stdin)
ips=data['Instances']['Instance'][0]['PublicIpAddress']['IpAddress']
print(ips[0] if ips else 'pending')
")
    
    info "公网 IP: $PUBLIC_IP"
}

# ============ 输出结果 ============
print_summary() {
    echo ""
    echo "============================================"
    echo -e "${GREEN}  Dream Recorder 云资源创建完成！${NC}"
    echo "============================================"
    echo ""
    echo "  VPC ID:       $VPC_ID"
    echo "  VSwitch ID:   $VSWITCH_ID"
    echo "  安全组 ID:    $SG_ID"
    echo "  ECS 实例 ID:  $INSTANCE_ID"
    echo "  公网 IP:      $PUBLIC_IP"
    echo ""
    echo "  SSH 登录:     ssh root@$PUBLIC_IP"
    echo "  前端地址:     http://$PUBLIC_IP:3000"
    echo "  后端 API:     http://$PUBLIC_IP:8000"
    echo ""
    echo "  下一步: 运行 deploy/setup-server.sh 初始化服务器"
    echo "============================================"
    
    # 保存到文件
    cat > deploy/.cloud-resources.env <<EOF
# 自动生成 - 云资源信息
REGION=$REGION
VPC_ID=$VPC_ID
VSWITCH_ID=$VSWITCH_ID
SG_ID=$SG_ID
INSTANCE_ID=$INSTANCE_ID
PUBLIC_IP=$PUBLIC_IP
EOF
    
    info "资源信息已保存到 deploy/.cloud-resources.env"
}

# ============ 主流程 ============
main() {
    echo "============================================"
    echo "  Dream Recorder - 阿里云资源开设"
    echo "============================================"
    echo ""
    check_prerequisites
    create_vpc
    create_security_group
    create_ecs
    print_summary
}

main "$@"
