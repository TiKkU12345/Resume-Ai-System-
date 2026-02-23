from werkzeug.security import generate_password_hash
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Apna admin password yahan dalo
ADMIN_EMAIL = "arunav.jsr.0604@gmail.com"
ADMIN_PASSWORD = "Admin@123"  # Change this!
ADMIN_NAME = "Arunav"

# Password hash banao
hashed_password = generate_password_hash(ADMIN_PASSWORD)
print(f"✓ Password hashed: {hashed_password[:50]}...")

# Database connect karo
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    print("✓ Database connected successfully!")
    
    # Step 1: is_admin column add karo
    cur.execute("""
        ALTER TABLE users 
        ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT false
    """)
    print("✓ Added is_admin column")
    
    # Step 2: Admin user banao ya update karo
    cur.execute("""
        INSERT INTO users (
            full_name, 
            email, 
            password, 
            is_approved, 
            is_admin,
            approved_at,
            created_at,
            device_id
        ) VALUES (%s, %s, %s, true, true, NOW(), NOW(), 'admin-device-001')
        ON CONFLICT (email) 
        DO UPDATE SET 
            is_admin = true, 
            password = EXCLUDED.password,
            is_approved = true
    """, (ADMIN_NAME, ADMIN_EMAIL, hashed_password))
    
    conn.commit()
    print("✓ Admin user created/updated successfully!")
    
    # Verify admin user
    cur.execute("SELECT id, full_name, email, is_admin FROM users WHERE email = %s", (ADMIN_EMAIL,))
    admin = cur.fetchone()
    print(f"\n✓ Admin User Details:")
    print(f"  ID: {admin[0]}")
    print(f"  Name: {admin[1]}")
    print(f"  Email: {admin[2]}")
    print(f"  Is Admin: {admin[3]}")
    
    cur.close()
    conn.close()
    
    print("\n🎉 Setup completed successfully!")
    print(f"\n📝 Admin Login Credentials:")
    print(f"   Email: {ADMIN_EMAIL}")
    print(f"   Password: {ADMIN_PASSWORD}")
    print(f"\n🌐 Access admin panel at: http://localhost:5000/admin")
    
except Exception as e:
    print(f"❌ Error: {e}")