#!/bin/bash
# 批量重置用户密码示例脚本
# 使用方法: ./batch_reset_example.sh

# 激活虚拟环境
source venv/bin/activate

# 要重置密码的用户ID列表
USER_IDS=(1 2 3 4 5)

# 新密码（建议使用环境变量或更安全的方式）
NEW_PASSWORD="newpassword123"

echo "🔐 批量重置用户密码"
echo "=================="
echo "目标用户: ${USER_IDS[@]}"
echo "新密码: $NEW_PASSWORD"
echo ""

# 确认操作
read -p "是否继续？(y/N): " confirm
if [[ $confirm != [yY] ]]; then
    echo "❌ 操作已取消"
    exit 0
fi

# 批量重置
for user_id in "${USER_IDS[@]}"; do
    echo ""
    echo "🔄 正在重置用户 $user_id 的密码..."
    
    # 使用 --force 跳过确认，--password 指定新密码
    python scripts/reset_user_password.py $user_id --force --password "$NEW_PASSWORD"
    
    if [ $? -eq 0 ]; then
        echo "✅ 用户 $user_id 密码重置成功"
    else
        echo "❌ 用户 $user_id 密码重置失败"
    fi
    
    echo "---"
done

echo ""
echo "🎉 批量重置完成！"
echo "请检查上述输出确认所有操作是否成功"
