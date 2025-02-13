from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import jwt
from datetime import datetime, timezone, timedelta
import os
from functools import wraps, lru_cache
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import json
from PIL import Image
from io import BytesIO
from decimal import Decimal
from flask.json import JSONEncoder

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:8080", "http://167.99.157.245"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"]
    }
})

# Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'fallback-secret-key')
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE')
}

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database connection helper with error handling
def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"Database connection failed: {err}")
        raise

# Token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM users WHERE id = %s', (data['user_id'],))
            current_user = cursor.fetchone()
            cursor.close()
            conn.close()
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

app.json_encoder = CustomJSONEncoder

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    print("Received registration data:", data)  # Debug print
    
    if not all(k in data for k in ['email', 'password', 'name']):
        missing_fields = [k for k in ['email', 'password', 'name'] if k not in data]
        return jsonify({
            'message': 'Missing required fields',
            'missing_fields': missing_fields
        }), 400
    
    # Validate that none of the fields are empty
    if not all(data.get(k) for k in ['email', 'password', 'name']):
        empty_fields = [k for k in ['email', 'password', 'name'] if not data.get(k)]
        return jsonify({
            'message': 'Required fields cannot be empty',
            'empty_fields': empty_fields
        }), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user already exists
        cursor.execute('SELECT * FROM users WHERE email = %s', (data['email'],))
        if cursor.fetchone():
            return jsonify({'message': 'User already exists'}), 409
        
        # Create new user
        hashed_password = generate_password_hash(data['password'], method='sha256')
        insert_query = '''
            INSERT INTO users (email, password, name, created_at) 
            VALUES (%s, %s, %s, %s)
        '''
        values = (data['email'], hashed_password, data['name'], datetime.now(timezone.utc))
        
        print("Executing query:", insert_query)  # Debug print
        print("With values:", values)  # Debug print
        
        cursor.execute(insert_query, values)
        conn.commit()
        
        # Get the created user
        cursor.execute(
            'SELECT id, email, name, created_at FROM users WHERE email = %s', 
            (data['email'],)
        )
        user = cursor.fetchone()
        
        if not user:
            raise Exception("User was not created successfully")
        
        # Convert datetime to string for JSON serialization
        user['created_at'] = user['created_at'].isoformat()
        
        # Generate token
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.now(timezone.utc) + timedelta(days=7)
        }, app.config['SECRET_KEY'])
        
        return jsonify({
            'user': user,
            'token': token
        }), 201
        
    except mysql.connector.Error as err:
        print("MySQL Error:", err)  # Debug print
        return jsonify({
            'message': 'Database error occurred',
            'error': str(err)
        }), 500
        
    except Exception as e:
        print("Error during registration:", str(e))  # Debug print
        return jsonify({
            'message': 'Registration failed',
            'error': str(e)
        }), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not all(k in data for k in ['email', 'password']):
        return jsonify({'message': 'Missing required fields'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('SELECT id, email, name, password, is_host FROM users WHERE email = %s', (data['email'],))
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user['password'], data['password']):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Remove password from user dict
        user.pop('password', None)
        
        # Convert is_host to boolean
        user['is_host'] = bool(user['is_host'])
        
        # Generate token
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.now(timezone.utc) + timedelta(days=7)
        }, app.config['SECRET_KEY'])
        
        return jsonify({
            'user': user,
            'token': token
        })
        
    except Exception as e:
        print("Error during login:", str(e))
        return jsonify({
            'message': 'Login failed',
            'error': str(e)
        }), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get user data including is_host
        cursor.execute('SELECT id, name, email, is_host FROM users WHERE id = %s', (current_user['id'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        print("User data from DB:", user)  # Debug print
        
        # Convert is_host to boolean
        user['is_host'] = bool(user['is_host'])
        
        print("User data after boolean conversion:", user)  # Debug print
        
        return jsonify(user)
        
    except Exception as e:
        print("Error fetching user:", str(e))
        return jsonify({
            'message': 'Failed to fetch user data',
            'error': str(e)
        }), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/test-db', methods=['GET'])
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SHOW TABLES')
        tables = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({
            'message': 'Database connection successful',
            'tables': tables
        })
    except Exception as e:
        return jsonify({
            'message': 'Database connection failed',
            'error': str(e)
        }), 500

@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout(current_user):
    # In a more complex implementation, you might want to:
    # 1. Add the token to a blacklist
    # 2. Clear any server-side sessions
    # 3. Handle multiple devices/tokens
    
    return jsonify({
        'message': 'Successfully logged out'
    })

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Food Experience endpoints
@app.route('/api/host/food-experiences', methods=['POST'])
@token_required
def create_food_experience(current_user):
    try:
        # Debug logs
        print("Received form data:", request.form)
        print("Files:", request.files)
        
        # Extract and validate required fields
        required_fields = [
            'title', 'description', 'location_name', 'price_per_person',
            'cuisine_type', 'menu_description', 'address', 'zipcode',
            'city', 'state', 'latitude', 'longitude'
        ]
        
        data = {}
        for field in required_fields:
            value = request.form.get(field)
            if not value:
                return jsonify({
                    'message': f'Missing required field: {field}',
                    'field': field
                }), 400
            data[field] = value

        # Create the experience
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        insert_query = '''
            INSERT INTO food_experiences (
                host_id, title, description, location_name,
                price_per_person, cuisine_type, menu_description,
                status, address, zipcode, city, state,
                latitude, longitude, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, NOW(), NOW()
            )
        '''
        
        values = (
            current_user['id'],
            data['title'],
            data['description'],
            data['location_name'],
            float(data['price_per_person']),
            data['cuisine_type'],
            data['menu_description'],
            request.form.get('status', 'draft'),
            data['address'],
            data['zipcode'],
            data['city'],
            data['state'],
            float(data['latitude']),
            float(data['longitude'])
        )

        cursor.execute(insert_query, values)
        experience_id = cursor.lastrowid

        # Handle image uploads
        image_urls = request.form.get('images', '').split(',') if request.form.get('images') else []
        print("Processing images:", image_urls)
        
        for index, image_url in enumerate(image_urls):
            if image_url and image_url.strip():
                filename = image_url.strip().split('/')[-1]
                print(f"Adding image to DB: {filename}")
                
                cursor.execute('''
                    INSERT INTO food_experience_images 
                    (experience_id, image_path, created_at, display_order) 
                    VALUES (%s, %s, %s, %s)
                ''', (experience_id, filename, datetime.now(timezone.utc), index))
        
        conn.commit()
        
        return jsonify({
            'message': 'Food experience created successfully',
            'id': experience_id
        }), 201
        
    except Exception as e:
        print("Error creating food experience:", str(e))
        if 'conn' in locals():
            conn.rollback()
        return jsonify({
            'message': 'Failed to create food experience',
            'error': str(e)
        }), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/host/food-experiences/<int:id>', methods=['PUT'])
@token_required
def update_host_food_experience(current_user, id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verify ownership
        cursor.execute('SELECT host_id FROM food_experiences WHERE id = %s', (id,))
        experience = cursor.fetchone()
        if not experience or experience['host_id'] != current_user['id']:
            return jsonify({'message': 'Experience not found or unauthorized'}), 404

        data = request.form.to_dict()
        print("Received form data:", data)  # Debug print
        
        # Update food experience
        update_query = """
            UPDATE food_experiences SET
                title = %s,
                description = %s,
                location_name = %s,
                price_per_person = %s,
                cuisine_type = %s,
                menu_description = %s,
                status = %s,
                address = %s,
                zipcode = %s,
                city = %s,
                state = %s,
                latitude = %s,
                longitude = %s,
                updated_at = NOW()
            WHERE id = %s AND host_id = %s
        """
        
        values = (
            data['title'],
            data['description'],
            data['location_name'],
            float(data['price_per_person']),
            data['cuisine_type'],
            data['menu_description'],
            data['status'],
            data['address'],
            data['zipcode'],
            data['city'],
            data['state'],
            float(data['latitude']),
            float(data['longitude']),
            id,
            current_user['id']
        )
        
        cursor.execute(update_query, values)
        
        # Handle images
        if 'images[]' in request.form:
            try:
                # Get all image URLs from form data
                image_urls = request.form.getlist('images[]')
                print("Processing images:", image_urls)  # Debug print
                
                # Delete old images
                cursor.execute('DELETE FROM food_experience_images WHERE experience_id = %s', (id,))
                
                # Insert new images
                for i, image_url in enumerate(image_urls):
                    if image_url:  # Only process non-empty URLs
                        filename = image_url.split('/')[-1]  # Extract filename from URL
                        print(f"Adding image {i}: {filename}")  # Debug print
                        cursor.execute("""
                            INSERT INTO food_experience_images 
                            (experience_id, image_path, display_order) 
                            VALUES (%s, %s, %s)
                        """, (id, filename, i))
            except Exception as e:
                print("Error processing images:", str(e))
                # Continue with the update even if image processing fails

        conn.commit()

        # Fetch and return the updated experience
        cursor.execute("""
            SELECT 
                fe.*,
                GROUP_CONCAT(DISTINCT fei.image_path ORDER BY fei.display_order) as image_paths
            FROM food_experiences fe
            LEFT JOIN food_experience_images fei ON fe.id = fei.experience_id
            WHERE fe.id = %s AND fe.host_id = %s
            GROUP BY fe.id
        """, (id, current_user['id']))
        
        updated_exp = cursor.fetchone()
        
        if updated_exp:
            # Format images
            images = []
            if updated_exp['image_paths']:
                for img_path in updated_exp['image_paths'].split(','):
                    if img_path:
                        images.append({'url': f"http://localhost:5000/uploads/{img_path}"})
            
            response = {
                'id': updated_exp['id'],
                'title': updated_exp['title'],
                'description': updated_exp['description'],
                'menu_description': updated_exp['menu_description'],
                'location_name': updated_exp['location_name'],
                'price_per_person': float(updated_exp['price_per_person']),
                'cuisine_type': updated_exp['cuisine_type'],
                'status': updated_exp['status'],
                'address': updated_exp['address'],
                'zipcode': updated_exp['zipcode'],
                'city': updated_exp['city'],
                'state': updated_exp['state'],
                'latitude': float(updated_exp['latitude']),
                'longitude': float(updated_exp['longitude']),
                'images': images
            }
            
            return jsonify(response)
            
        return jsonify({'message': 'Failed to fetch updated experience'}), 500
        
    except Exception as e:
        print("Error updating food experience:", str(e))
        if 'conn' in locals():
            conn.rollback()
        return jsonify({'message': 'Failed to update experience', 'error': str(e)}), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    return obj

@app.route('/api/host/food-experiences', methods=['GET'])
@token_required
def get_host_food_experiences(current_user):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT 
                fe.*,
                GROUP_CONCAT(DISTINCT fei.image_path) as image_paths
            FROM food_experiences fe
            LEFT JOIN food_experience_images fei ON fe.id = fei.experience_id
            WHERE fe.host_id = %s
            GROUP BY fe.id
            ORDER BY fe.created_at DESC
        """
        
        cursor.execute(query, (current_user['id'],))
        experiences = cursor.fetchall()
        
        # Process the results
        for exp in experiences:
            # Handle images
            image_paths = exp.pop('image_paths', '')
            
            if image_paths and image_paths.strip():
                # Only include images that exist in the uploads folder
                valid_images = []
                for path in image_paths.split(','):
                    # Clean the path by removing any order numbers after ':'
                    clean_path = path.split(':')[0].strip()
                    if clean_path:
                        full_path = os.path.join(UPLOAD_FOLDER, clean_path)
                        if os.path.exists(full_path):
                            valid_images.append({
                                'url': f'http://localhost:5000/uploads/{clean_path}'
                            })
                exp['images'] = valid_images
            else:
                exp['images'] = []
            
            # Convert decimal values to float for JSON serialization
            if 'price_per_person' in exp:
                exp['price_per_person'] = float(exp['price_per_person'])
            if 'latitude' in exp:
                exp['latitude'] = float(exp['latitude']) if exp['latitude'] else 0
            if 'longitude' in exp:
                exp['longitude'] = float(exp['longitude']) if exp['longitude'] else 0
            
            # Convert datetime objects to strings
            if 'created_at' in exp:
                exp['created_at'] = exp['created_at'].isoformat()
            if 'updated_at' in exp:
                exp['updated_at'] = exp['updated_at'].isoformat()
        
        return jsonify(experiences)
        
    except Exception as e:
        print("Error fetching experiences:", str(e))
        return jsonify({
            'message': 'Failed to fetch experiences',
            'error': str(e)
        }), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/host/food-experiences/<int:id>/images', methods=['DELETE'])
@token_required
def delete_food_experience_image(current_user, id):
    try:
        data = request.get_json()
        image_url = data.get('imageUrl')
        if not image_url:
            return jsonify({'message': 'Image URL is required'}), 400

        # Extract filename from URL
        filename = image_url.split('/')[-1]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Verify ownership
        cursor.execute('''
            SELECT fe.host_id 
            FROM food_experiences fe 
            JOIN food_experience_images fei ON fe.id = fei.experience_id 
            WHERE fe.id = %s AND fei.image_path = %s
        ''', (id, filename))
        
        result = cursor.fetchone()
        if not result or result['host_id'] != current_user['id']:
            return jsonify({'message': 'Image not found or unauthorized'}), 404

        # Delete image record
        cursor.execute('''
            DELETE FROM food_experience_images 
            WHERE experience_id = %s AND image_path = %s
        ''', (id, filename))

        # Reorder remaining images
        cursor.execute('''
            SET @order := -1;
            UPDATE food_experience_images 
            SET display_order = (@order := @order + 1)
            WHERE experience_id = %s 
            ORDER BY created_at;
        ''', (id,))

        conn.commit()

        # Delete actual file
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")

        return jsonify({'message': 'Image deleted successfully'})

    except Exception as e:
        print("Error deleting image:", str(e))
        if 'conn' in locals():
            conn.rollback()
        return jsonify({
            'message': 'Failed to delete image',
            'error': str(e)
        }), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/host/food-experiences/<int:id>/images/reorder', methods=['POST'])
@token_required
def reorder_food_experience_images(current_user, id):
    try:
        data = request.get_json()
        image_order = data.get('imageOrder', [])

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Verify ownership
        cursor.execute('SELECT host_id FROM food_experiences WHERE id = %s', (id,))
        experience = cursor.fetchone()
        if not experience or experience['host_id'] != current_user['id']:
            return jsonify({'message': 'Experience not found or unauthorized'}), 404

        # Update order for each image
        for index, image_url in enumerate(image_order):
            filename = image_url.split('/')[-1]
            cursor.execute('''
                UPDATE food_experience_images 
                SET display_order = %s 
                WHERE experience_id = %s AND image_path = %s
            ''', (index, id, filename))

        conn.commit()
        return jsonify({'message': 'Image order updated successfully'})

    except Exception as e:
        print("Error reordering images:", str(e))
        if 'conn' in locals():
            conn.rollback()
        return jsonify({
            'message': 'Failed to reorder images',
            'error': str(e)
        }), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Stay endpoints
@app.route('/api/host/stays', methods=['POST'])
@token_required
def create_stay(current_user):
    try:
        data = request.form.to_dict()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Insert stay
        insert_query = '''
            INSERT INTO stays (
                host_id, title, description, location_name,
                price_per_night, max_guests, bedrooms,
                created_at, updated_at, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        values = (
            current_user['id'], data['title'], data['description'],
            data['location_name'], float(data['price_per_night']),
            int(data['max_guests']), int(data['bedrooms']),
            datetime.now(timezone.utc), datetime.now(timezone.utc),
            data.get('status', 'draft')
        )
        
        cursor.execute(insert_query, values)
        stay_id = cursor.lastrowid

        # Handle images
        if 'images' in data:
            image_urls = data['images'].split(',') if data['images'] else []
            for index, image_url in enumerate(image_urls):
                if image_url and image_url.strip():
                    filename = image_url.strip().split('/')[-1]
                    cursor.execute('''
                        INSERT INTO stay_images 
                        (stay_id, image_path, created_at, display_order) 
                        VALUES (%s, %s, %s, %s)
                    ''', (stay_id, filename, datetime.now(timezone.utc), index))

        conn.commit()
        return jsonify({
            'message': 'Stay created successfully',
            'id': stay_id
        }), 201

    except Exception as e:
        print("Error creating stay:", str(e))
        if 'conn' in locals():
            conn.rollback()
        return jsonify({
            'message': 'Failed to create stay',
            'error': str(e)
        }), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/host/stays', methods=['GET'])
@token_required
def get_host_stays(current_user):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT 
                s.*,
                GROUP_CONCAT(
                    CONCAT(si.image_path, ':', COALESCE(si.display_order, 0))
                    ORDER BY si.display_order ASC
                ) as image_data,
                GROUP_CONCAT(DISTINCT sa.amenity_id) as amenities
            FROM stays s
            LEFT JOIN stay_images si ON s.id = si.stay_id
            LEFT JOIN stay_amenities sa ON s.id = sa.stay_id
            WHERE s.host_id = %s
            GROUP BY s.id
            ORDER BY s.created_at DESC
        ''', (current_user['id'],))
        
        stays = cursor.fetchall()
        
        # Process the results
        for stay in stays:
            stay['created_at'] = stay['created_at'].isoformat()
            stay['updated_at'] = stay['updated_at'].isoformat()
            stay['price_per_night'] = float(stay['price_per_night'])
            
            # Process image data
            if stay['image_data']:
                image_list = []
                for img_data in stay['image_data'].split(','):
                    if ':' in img_data:
                        path, order = img_data.split(':')
                        image_list.append({
                            'url': f"http://localhost:5000/uploads/{path.strip()}",
                            'order': int(order)
                        })
                stay['images'] = sorted(image_list, key=lambda x: x['order'])
            else:
                stay['images'] = []
                
            # Process amenities
            if stay['amenities']:
                stay['amenities'] = [int(x) for x in stay['amenities'].split(',')]
            else:
                stay['amenities'] = []
        
        return jsonify(stays)
        
    except Exception as e:
        print("Error fetching stays:", str(e))
        return jsonify({
            'message': 'Failed to fetch stays',
            'error': str(e)
        }), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/host/stays/<int:id>', methods=['PUT'])
@token_required
def update_stay(current_user, id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verify ownership
        cursor.execute('SELECT host_id FROM stays WHERE id = %s', (id,))
        stay = cursor.fetchone()
        if not stay or stay['host_id'] != current_user['id']:
            return jsonify({'message': 'Stay not found or unauthorized'}), 404

        data = request.form.to_dict()
        
        # Update stay
        update_query = '''
            UPDATE stays SET
                title = %s,
                description = %s,
                location_name = %s,
                price_per_night = %s,
                max_guests = %s,
                bedrooms = %s,
                bathrooms = %s,
                status = %s,
                address = %s,
                zipcode = %s,
                city = %s,
                state = %s,
                latitude = %s,
                longitude = %s,
                updated_at = NOW()
            WHERE id = %s
        '''
        values = (
            data['title'],
            data['description'],
            data['location_name'],
            float(data['price_per_night']),
            int(data['max_guests']),
            int(data['bedrooms']),
            int(data.get('bathrooms', data['bedrooms'])),  # Default to bedrooms count
            data['status'],
            data['address'],
            data['zipcode'],
            data['city'],
            data['state'],
            float(data['latitude']),
            float(data['longitude']),
            id
        )
        cursor.execute(update_query, values)

        # Update amenities
        if 'amenities' in data:
            amenities = json.loads(data['amenities'])
            cursor.execute('DELETE FROM stay_amenities WHERE stay_id = %s', (id,))
            for amenity_id in amenities:
                cursor.execute(
                    'INSERT INTO stay_amenities (stay_id, amenity_id) VALUES (%s, %s)',
                    (id, amenity_id)
                )

        # Update availability
        if 'availability' in data:
            availability = json.loads(data['availability'])
            cursor.execute('DELETE FROM stay_availability WHERE stay_id = %s', (id,))
            for avail in availability:
                cursor.execute('''
                    INSERT INTO stay_availability 
                    (stay_id, date, is_available, price_override, created_at, updated_at) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    id, 
                    avail['date'],
                    avail['is_available'],
                    avail.get('price_override', None),
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc)
                ))

        # Update images if provided
        if 'images' in request.files:
            images = request.files.getlist('images')
            cursor.execute('DELETE FROM stay_images WHERE stay_id = %s', (id,))
            for i, image in enumerate(images):
                if image and allowed_file(image.filename):
                    filename = secure_filename(f"{id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.jpg")
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    cursor.execute('''
                        INSERT INTO stay_images 
                        (stay_id, image_path, display_order, created_at) 
                        VALUES (%s, %s, %s, NOW())
                    ''', (id, filename, i))

        conn.commit()

        # Fetch and return the updated stay
        cursor.execute('''
            SELECT 
                s.*,
                u.name as host_name,
                GROUP_CONCAT(
                    DISTINCT CONCAT(si.image_path, ':', COALESCE(si.display_order, 0))
                    ORDER BY si.display_order ASC
                ) as image_data,
                GROUP_CONCAT(DISTINCT sa.amenity_id) as amenities,
                GROUP_CONCAT(
                    DISTINCT CONCAT(
                        sav.date, ' ',
                        COALESCE(sav.price_override, s.price_per_night), ' ',
                        sav.is_available
                    )
                ) as availability_data
            FROM stays s
            JOIN users u ON s.host_id = u.id
            LEFT JOIN stay_images si ON s.id = si.stay_id
            LEFT JOIN stay_amenities sa ON s.id = sa.stay_id
            LEFT JOIN stay_availability sav ON s.id = sav.stay_id
            WHERE s.id = %s
            GROUP BY s.id
        ''', (id,))
        
        updated_stay = cursor.fetchone()
        
        # Process the updated stay data
        if updated_stay:
            updated_stay['price_per_night'] = float(updated_stay['price_per_night'])
            updated_stay['created_at'] = updated_stay['created_at'].isoformat()
            updated_stay['updated_at'] = updated_stay['updated_at'].isoformat()
            
            # Process images
            images = []
            if updated_stay['image_data']:
                for img_data in updated_stay['image_data'].split(','):
                    path, order = img_data.split(':')
                    images.append({
                        'url': f"http://localhost:5000/uploads/{path}",
                        'order': int(order)
                    })
            updated_stay['images'] = images
            
            # Process amenities
            updated_stay['amenities'] = updated_stay['amenities'].split(',') if updated_stay['amenities'] else []
            
            # Process availability
            availability = []
            if updated_stay['availability_data']:
                for avail_data in updated_stay['availability_data'].split(','):
                    date, price, is_available = avail_data.split(' ')
                    availability.append({
                        'date': date,
                        'price': float(price),
                        'is_available': bool(int(is_available))
                    })
            updated_stay['availability'] = availability
            
            # Clean up response
            del updated_stay['image_data']
            del updated_stay['availability_data']
            
        return jsonify({
            'message': 'Stay updated successfully',
            'stay': updated_stay
        }), 200

    except Exception as e:
        print("Error updating stay:", str(e))
        if 'conn' in locals():
            conn.rollback()
        return jsonify({'message': 'Failed to update stay', 'error': str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Amenities endpoints
@app.route('/api/amenities', methods=['GET'])
def get_amenities():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get amenities by type (stay, food, or both)
        amenity_type = request.args.get('type', 'both')
        
        if amenity_type in ['stay', 'food']:
            cursor.execute('''
                SELECT * FROM amenities 
                WHERE type = %s OR type = 'both'
                ORDER BY category, name
            ''', (amenity_type,))
        else:
            cursor.execute('SELECT * FROM amenities ORDER BY category, name')
            
        amenities = cursor.fetchall()
        
        # Group amenities by category
        grouped_amenities = {}
        for amenity in amenities:
            category = amenity['category'] or 'Other'
            if category not in grouped_amenities:
                grouped_amenities[category] = []
            grouped_amenities[category].append({
                'id': str(amenity['id']),
                'name': amenity['name']
            })
            
        return jsonify(grouped_amenities)
        
    except Exception as e:
        print("Error fetching amenities:", str(e))
        return jsonify({
            'message': 'Failed to fetch amenities',
            'error': str(e)
        }), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/host/stays/<int:id>/availability', methods=['POST'])
@token_required
def update_stay_availability(current_user, id):
    try:
        data = request.get_json()
        dates = data.get('dates', [])
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verify ownership
        cursor.execute('SELECT host_id FROM stays WHERE id = %s', (id,))
        stay = cursor.fetchone()
        if not stay or stay['host_id'] != current_user['id']:
            return jsonify({'message': 'Stay not found or unauthorized'}), 404
            
        # Update availability
        for date_info in dates:
            cursor.execute('''
                INSERT INTO stay_availability 
                (stay_id, date, is_available, price_override, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                is_available = VALUES(is_available),
                price_override = VALUES(price_override),
                updated_at = VALUES(updated_at)
            ''', (
                id, 
                date_info['date'],
                date_info['is_available'],
                date_info.get('price_override'),
                datetime.now(timezone.utc),
                datetime.now(timezone.utc)
            ))
            
        conn.commit()
        return jsonify({'message': 'Availability updated successfully'})
        
    except Exception as e:
        print("Error updating availability:", str(e))
        if 'conn' in locals():
            conn.rollback()
        return jsonify({
            'message': 'Failed to update availability',
            'error': str(e)
        }), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def optimize_image(image_file):
    try:
        img = Image.open(image_file)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Calculate new dimensions while maintaining aspect ratio
        max_size = 1920
        ratio = min(max_size/float(img.size[0]), max_size/float(img.size[1]))
        if ratio < 1:
            new_size = tuple([int(x*ratio) for x in img.size])
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save optimized image
        output = BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        return output
        
    except Exception as e:
        print(f"Error optimizing image: {e}")
        return image_file

@app.route('/api/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    if 'image' not in request.files:
        print("No image in request files")
        return jsonify({'error': 'No image part'}), 400
        
    file = request.files['image']
    title = request.form.get('title', '')
    
    print(f"Processing upload for title: {title}")
    
    if file.filename == '':
        print("Empty filename")
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        try:
            # Create uploads directory if it doesn't exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Optimize image
            optimized = optimize_image(file)
            
            # Generate filename using title and original extension
            safe_title = secure_filename(title) if title else 'untitled'
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            original_ext = os.path.splitext(file.filename)[1]
            filename = f"{safe_title}_{timestamp}{original_ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            print(f"Saving file as: {filename}")
            
            # Save optimized image
            with open(filepath, 'wb') as f:
                f.write(optimized.getvalue() if isinstance(optimized, BytesIO) else optimized.read())
            
            # Return absolute URL in production
            url = f"/uploads/{filename}"
            if os.getenv('FLASK_ENV') == 'production':
                url = f"http://167.99.157.245{url}"
            
            return jsonify({
                'url': url,
                'message': 'File uploaded successfully'
            })
            
        except Exception as e:
            print(f"Error during upload: {str(e)}")
            return jsonify({
                'error': 'Error uploading file',
                'message': str(e)
            }), 500
    else:
        print(f"Invalid file type: {file.filename}")
        return jsonify({'error': f'File type not allowed. Allowed types are: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

# Add this to serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/food-experiences', methods=['GET'])
def get_food_experiences():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Base query
        query = """
            SELECT 
                fe.*,
                u.name as host_name,
                COALESCE(AVG(r.rating), 0) as rating,
                COUNT(DISTINCT r.id) as reviews_count,
                GROUP_CONCAT(DISTINCT fei.image_path) as image_paths
            FROM food_experiences fe
            LEFT JOIN users u ON fe.host_id = u.id
            LEFT JOIN reviews r ON fe.id = r.experience_id
            LEFT JOIN food_experience_images fei ON fe.id = fei.experience_id 
            WHERE fe.status = 'published'
        """
        params = []

        # Add zipcode filter if provided
        zipcode = request.args.get('zipcode')
        if zipcode:
            query += " AND fe.zipcode = %s"
            params.append(zipcode)

        # Group by and sort
        query += " GROUP BY fe.id"
        
        sort = request.args.get('sort', 'rating_desc')
        if sort == 'rating_desc':
            query += " ORDER BY rating DESC"
        elif sort == 'price_asc':
            query += " ORDER BY fe.price_per_person ASC"
        elif sort == 'price_desc':
            query += " ORDER BY fe.price_per_person DESC"

        cursor.execute(query, params)
        experiences = cursor.fetchall()
        
        # Process the results
        for exp in experiences:
            # Handle images
            image_paths = exp.pop('image_paths', '')
            
            if image_paths and image_paths.strip():
                # Only include images that exist in the uploads folder
                valid_images = []
                for path in image_paths.split(','):
                    # Clean the path by removing any order numbers after ':'
                    clean_path = path.split(':')[0].strip()
                    if clean_path:
                        full_path = os.path.join(UPLOAD_FOLDER, clean_path)
                        if os.path.exists(full_path):
                            valid_images.append({
                                'url': f'http://localhost:5000/uploads/{clean_path}'
                            })
                exp['images'] = valid_images
            else:
                exp['images'] = []  # Empty array if no images
            
            # Format host info
            exp['host'] = {
                'name': exp.pop('host_name', 'Unknown Host'),
                'rating': float(exp.pop('rating', 0)),
                'reviews': int(exp.pop('reviews_count', 0))
            }
            
            # Convert decimal values to float/int
            exp['price_per_person'] = float(exp['price_per_person'])
            exp['latitude'] = float(exp['latitude']) if exp['latitude'] else 0
            exp['longitude'] = float(exp['longitude']) if exp['longitude'] else 0
            
            # Ensure all required fields have default values
            exp['location_name'] = exp['location_name'] or 'Location not specified'
            exp['cuisine_type'] = exp['cuisine_type'] or 'Various'
            exp['description'] = exp['description'] or 'No description available'
        
        return jsonify(experiences)
        
    except Exception as e:
        print("Error fetching food experiences:", str(e))
        return jsonify({'error': 'Failed to fetch food experiences'}), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@lru_cache(maxsize=100)
def get_optimized_image_path(original_path):
    """Create and cache optimized thumbnails for images"""
    try:
        if not original_path:
            return None
            
        # Check if original image exists
        original_full_path = os.path.join(UPLOAD_FOLDER, original_path)
        if not os.path.exists(original_full_path):
            return None
            
        # Create thumbnails directory if it doesn't exist
        thumb_dir = os.path.join(UPLOAD_FOLDER, 'thumbnails')
        os.makedirs(thumb_dir, exist_ok=True)
        
        # Generate thumbnail path
        filename = os.path.basename(original_path)
        thumb_path = os.path.join(thumb_dir, f'thumb_{filename}')
        
        # If thumbnail doesn't exist, create it
        if not os.path.exists(thumb_path):
            with Image.open(original_full_path) as img:
                img.thumbnail(THUMBNAIL_SIZE)
                img.save(thumb_path, 'JPEG', quality=85, optimize=True)
        
        return f'thumbnails/thumb_{filename}'
        
    except Exception as e:
        print(f"Error optimizing image {original_path}: {str(e)}")
        return None

@app.route('/api/stays', methods=['GET'])
def get_stays():
    try:
        # Get query parameters
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', 10, type=float)
        sort_by = request.args.get('sort', 'price_asc')
        min_price = request.args.get('min_price', 0, type=float)
        max_price = request.args.get('max_price', 1000, type=float)
        min_guests = request.args.get('min_guests', 1, type=int)
        amenities = request.args.getlist('amenities')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if reviews table exists
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables 
            WHERE table_schema = 'platform2025' 
            AND table_name = 'reviews'
        """)
        reviews_exist = cursor.fetchone()['COUNT(*)'] > 0

        # Base query
        query = """
            SELECT 
                s.*,
                u.name as host_name,
                '' as host_image,
                JSON_OBJECT(
                    'bedrooms', s.bedrooms,
                    'bathrooms', s.bedrooms,  /* Use bedrooms as fallback for bathrooms */
                    'maxGuests', s.max_guests,
                    'location', s.location_name
                ) as details,
                JSON_OBJECT(
                    'name', u.name,
                    'image', COALESCE(u.image, ''),
                    'rating', COALESCE(AVG(r.rating), 4.5),
                    'reviews', COALESCE(COUNT(DISTINCT r.id), 0)
                ) as host_data
        """

        if reviews_exist:
            query += """,
                COUNT(DISTINCT r.id) as review_count
            """
        else:
            query += """,
                0 as review_count
            """

        # Add distance calculation if location is provided
        if lat and lng:
            query += f""",
                (6371 * acos(
                    cos(radians({lat})) * cos(radians(latitude)) *
                    cos(radians(longitude) - radians({lng})) +
                    sin(radians({lat})) * sin(radians(latitude))
                )) as distance
            """

        query += """
            FROM stays s
            JOIN users u ON s.host_id = u.id
        """

        if reviews_exist:
            query += " LEFT JOIN reviews r ON s.id = r.stay_id"

        # Add amenities join if needed
        if amenities:
            query += """
                JOIN stay_amenities sa ON s.id = sa.stay_id
                JOIN amenities a ON sa.amenity_id = a.id
            """

        query += """
            WHERE s.status = 'published'
            AND s.price_per_night BETWEEN %s AND %s
            AND s.max_guests >= %s
        """

        params = [min_price, max_price, min_guests]

        if amenities:
            query += f" AND a.name IN ({','.join(['%s'] * len(amenities))})"
            params.extend(amenities)

        query += " GROUP BY s.id"

        # Add distance filter if location is provided
        if lat and lng:
            query += f" HAVING distance <= {radius}"

        # Add sorting
        if sort_by == 'price_asc':
            query += " ORDER BY s.price_per_night ASC"
        elif sort_by == 'price_desc':
            query += " ORDER BY s.price_per_night DESC"
        elif sort_by == 'rating_desc' and reviews_exist:
            query += " ORDER BY review_count DESC"
        elif sort_by == 'distance_asc' and lat and lng:
            query += " ORDER BY distance ASC"
        else:
            query += " ORDER BY s.created_at DESC"

        cursor.execute(query, params)
        stays = cursor.fetchall()

        # Process the results
        for stay in stays:
            # Convert decimal values to float for JSON serialization
            stay['price_per_night'] = float(stay['price_per_night'])
            stay['created_at'] = stay['created_at'].isoformat()
            stay['updated_at'] = stay['updated_at'].isoformat()
            stay['details'] = json.loads(stay['details'])
            stay['host'] = json.loads(stay['host_data'])
            del stay['host_data']  # Clean up temporary field
            del stay['host_name']  # Clean up redundant field
            del stay['host_image']  # Clean up redundant field

            # Fetch images
            cursor.execute("""
                SELECT image_path 
                FROM stay_images 
                WHERE stay_id = %s 
                ORDER BY display_order
            """, (stay['id'],))
            stay['images'] = [row['image_path'] for row in cursor.fetchall()]

            # Fetch amenities
            cursor.execute("""
                SELECT a.name, a.category
                FROM amenities a
                JOIN stay_amenities sa ON a.id = sa.amenity_id
                WHERE sa.stay_id = %s
            """, (stay['id'],))
            stay['amenities'] = cursor.fetchall()

        return jsonify(stays)

    except Exception as e:
        print("Error fetching stays:", str(e))
        return jsonify({'error': 'Failed to fetch stays'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/food-experiences/<int:id>', methods=['GET'])
def get_food_experience(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get food experience details
        cursor.execute("""
            SELECT 
                fe.*,
                u.name as host_name,
                u.image as host_image,
                COALESCE(AVG(r.rating), 0) as rating,
                COUNT(DISTINCT r.id) as reviews_count,
                GROUP_CONCAT(DISTINCT fei.image_path) as image_paths
            FROM food_experiences fe
            LEFT JOIN users u ON fe.host_id = u.id
            LEFT JOIN reviews r ON fe.id = r.experience_id
            LEFT JOIN food_experience_images fei ON fe.id = fei.experience_id
            WHERE fe.id = %s AND fe.status = 'published'
            GROUP BY fe.id
        """, (id,))
        
        experience = cursor.fetchone()
        
        if not experience:
            return jsonify({'message': 'Experience not found'}), 404
            
        # Handle image paths
        image_paths = experience['image_paths'].split(',') if experience['image_paths'] else []
        images = [{'url': f"http://localhost:5000/uploads/{img}"} for img in image_paths if img]
        
        # Format the response
        response = {
            'id': experience['id'],
            'title': experience['title'],
            'description': experience['description'],
            'menu_description': experience['menu_description'],
            'price_per_person': float(experience['price_per_person']),
            'cuisine_type': experience['cuisine_type'],
            'images': images,
            'host': {
                'name': experience['host_name'],
                'image': f"http://localhost:5000/uploads/{experience['host_image']}" if experience['host_image'] else '/default-avatar.png',
                'rating': float(experience['rating']),
                'reviews': experience['reviews_count']
            },
            'details': {
                'duration': experience.get('duration', '2 hours'),
                'groupSize': f"Up to {experience.get('max_guests', 8)} guests",
                'includes': ['All ingredients', 'Cooking equipment', 'Recipes to take home'],
                'language': experience.get('language', 'English'),
                'location': f"{experience['city']}, {experience['state']}"
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        print("Error fetching food experience:", str(e))
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/api/host/food-experiences/<int:id>', methods=['GET'])
@token_required
def get_host_food_experience_by_id(current_user, id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                fe.*,
                GROUP_CONCAT(DISTINCT fei.image_path) as image_paths
            FROM food_experiences fe
            LEFT JOIN food_experience_images fei ON fe.id = fei.experience_id
            WHERE fe.id = %s AND fe.host_id = %s
            GROUP BY fe.id
        """, (id, current_user['id']))
        
        experience = cursor.fetchone()
        
        if not experience:
            return jsonify({'message': 'Experience not found'}), 404
            
        # Format the response
        response = {
            'id': experience['id'],
            'title': experience['title'],
            'description': experience['description'],
            'menu_description': experience['menu_description'],
            'price_per_person': float(experience['price_per_person']),
            'cuisine_type': experience['cuisine_type'],
            'location_name': experience['location_name'],
            'address': experience['address'],
            'zipcode': experience['zipcode'],
            'city': experience['city'],
            'state': experience['state'],
            'latitude': float(experience['latitude']),
            'longitude': float(experience['longitude']),
            'status': experience['status'],
            'images': [{'url': img} for img in (experience['image_paths'].split(',') if experience['image_paths'] else [])],
            'duration': experience.get('duration', '2 hours'),
            'max_guests': experience.get('max_guests', 8),
            'language': experience.get('language', 'English')
        }
        
        return jsonify(response)
        
    except Exception as e:
        print("Error fetching host food experience:", str(e))
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/api/stays', methods=['GET'])
def get_published_stays():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get all published stays with their first image and host info
        cursor.execute('''
            SELECT 
                s.*,
                u.name as host_name,
                MIN(si.image_path) as image_path,
                GROUP_CONCAT(DISTINCT sa.amenity_id) as amenities
            FROM stays s
            JOIN users u ON s.host_id = u.id
            LEFT JOIN stay_images si ON s.id = si.stay_id
            LEFT JOIN stay_amenities sa ON s.id = sa.stay_id
            WHERE s.status = 'published'
            GROUP BY s.id
            ORDER BY s.created_at DESC
        ''')
        
        stays = cursor.fetchall()
        
        # Process the results
        for stay in stays:
            stay['price_per_night'] = float(stay['price_per_night'])
            stay['created_at'] = stay['created_at'].isoformat()
            stay['updated_at'] = stay['updated_at'].isoformat()
            
            # Format image URL
            if stay['image_path']:
                stay['image'] = f"http://localhost:5000/uploads/{stay['image_path']}"
            else:
                stay['image'] = None
                
            # Add host details
            stay['host'] = {
                'name': stay['host_name'],
                'image': '/default-avatar.png',
                'rating': 4.5,
                'reviews': 10
            }
            
            # Add details
            stay['details'] = {
                'bedrooms': stay['bedrooms'],
                'bathrooms': stay['bedrooms'],  # Assuming 1 bathroom per bedroom
                'maxGuests': stay['max_guests'],
                'amenities': stay['amenities'].split(',') if stay['amenities'] else [],
                'location': stay['location_name']
            }
            
            # Clean up response
            del stay['host_name']
            del stay['image_path']
            del stay['amenities']
            
        return jsonify(stays)
        
    except Exception as e:
        print("Error fetching stays:", str(e))
        return jsonify({
            'message': 'Failed to fetch stays',
            'error': str(e)
        }), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/featured-food', methods=['GET'])
def get_featured_food():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                fe.*,
                u.name as host_name,
                u.image as host_image,
                COALESCE(AVG(r.rating), 0) as rating,
                COUNT(DISTINCT r.id) as reviews_count,
                MIN(fei.image_path) as first_image
            FROM food_experiences fe
            LEFT JOIN users u ON fe.host_id = u.id
            LEFT JOIN reviews r ON fe.id = r.experience_id
            LEFT JOIN food_experience_images fei ON fe.id = fei.experience_id
            WHERE fe.status = 'published'
            GROUP BY fe.id
            ORDER BY rating DESC, reviews_count DESC
            LIMIT 6
        """)
        
        experiences = cursor.fetchall()
        
        # Format the response
        response = []
        for exp in experiences:
            # Get the first image for the card
            image_url = f"http://localhost:5000/uploads/{exp['first_image']}" if exp['first_image'] else '/default-food.jpg'
            
            response.append({
                'id': exp['id'],
                'title': exp['title'],
                'description': exp['description'],
                'price_per_person': float(exp['price_per_person']),
                'cuisine_type': exp['cuisine_type'],
                'image': image_url,  # Single image for the card
                'host': {
                    'name': exp['host_name'],
                    'image': f"http://localhost:5000/uploads/{exp['host_image']}" if exp['host_image'] else '/default-avatar.png',
                    'rating': float(exp['rating']),
                    'reviews': exp['reviews_count']
                },
                'location': f"{exp['city']}, {exp['state']}"
            })
        
        return jsonify(response)
        
    except Exception as e:
        print("Error fetching featured food:", str(e))
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/api/featured-stays', methods=['GET'])
def get_featured_stays():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get featured stays (limit to 4)
        cursor.execute('''
            SELECT 
                s.*,
                u.name as host_name,
                MIN(si.image_path) as image_path,
                GROUP_CONCAT(DISTINCT sa.amenity_id) as amenities
            FROM stays s
            JOIN users u ON s.host_id = u.id
            LEFT JOIN stay_images si ON s.id = si.stay_id
            LEFT JOIN stay_amenities sa ON s.id = sa.stay_id
            WHERE s.status = 'published' AND s.is_featured = TRUE
            GROUP BY s.id
            ORDER BY s.created_at DESC
            LIMIT 4
        ''')
        
        stays = cursor.fetchall()
        
        # Process the results (similar to get_published_stays)
        for stay in stays:
            stay['price_per_night'] = float(stay['price_per_night'])
            stay['created_at'] = stay['created_at'].isoformat()
            stay['updated_at'] = stay['updated_at'].isoformat()
            
            if stay['image_path']:
                stay['image'] = f"http://localhost:5000/uploads/{stay['image_path']}"
            else:
                stay['image'] = None
                
            stay['host'] = {
                'name': stay['host_name'],
                'image': '/default-avatar.png',
                'rating': 4.5,
                'reviews': 10
            }
            
            # Clean up response
            del stay['host_name']
            del stay['image_path']
            del stay['amenities']
            
        return jsonify(stays)
        
    except Exception as e:
        print("Error fetching featured stays:", str(e))
        return jsonify({
            'message': 'Failed to fetch featured stays',
            'error': str(e)
        }), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/food-categories', methods=['GET'])
def get_food_categories():
    categories = [
        {
            'id': 'local',
            'title': 'Local Cuisine',
            'description': 'Experience authentic local dishes',
            'image': '/images/categories/local.jpg'
        },
        {
            'id': 'baking',
            'title': 'Baking',
            'description': 'Learn to bake breads and pastries',
            'image': '/images/categories/baking.jpg'
        },
        {
            'id': 'vegetarian',
            'title': 'Vegetarian',
            'description': 'Discover plant-based cooking',
            'image': '/images/categories/vegetarian.jpg'
        },
        {
            'id': 'desserts',
            'title': 'Desserts',
            'description': 'Master sweet treats and desserts',
            'image': '/images/categories/desserts.jpg'
        }
    ]
    return jsonify(categories)

@app.route('/api/host/stays/<int:id>', methods=['GET'])
@token_required
def get_host_stay(current_user, id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if the stay exists and belongs to the host
        cursor.execute('''
            SELECT 
                s.*,
                GROUP_CONCAT(
                    DISTINCT CONCAT(si.image_path, ':', COALESCE(si.display_order, 0))
                    ORDER BY si.display_order ASC
                ) as image_data,
                GROUP_CONCAT(DISTINCT sa.amenity_id) as amenities,
                GROUP_CONCAT(
                    DISTINCT CONCAT(
                        sav.date, ' ',
                        COALESCE(sav.price_override, s.price_per_night), ' ',
                        sav.is_available
                    )
                ) as availability_data
            FROM stays s
            LEFT JOIN stay_images si ON s.id = si.stay_id
            LEFT JOIN stay_amenities sa ON s.id = sa.stay_id
            LEFT JOIN stay_availability sav ON s.id = sav.stay_id
            WHERE s.id = %s AND s.host_id = %s
            GROUP BY s.id
        ''', (id, current_user['id']))
        
        stay = cursor.fetchone()
        
        if not stay:
            return jsonify({'message': 'Stay not found or unauthorized'}), 404
            
        # Process the results
        stay['price_per_night'] = float(stay['price_per_night'])
        stay['created_at'] = stay['created_at'].isoformat()
        stay['updated_at'] = stay['updated_at'].isoformat()
        
        # Process images
        images = []
        if stay['image_data']:
            for img_data in stay['image_data'].split(','):
                path, order = img_data.split(':')
                images.append({
                    'url': f"http://localhost:5000/uploads/{path}",
                    'order': int(order)
                })
        stay['images'] = images
        
        # Process amenities
        stay['amenities'] = stay['amenities'].split(',') if stay['amenities'] else []
        
        # Process availability
        availability = []
        if stay['availability_data']:
            for avail_data in stay['availability_data'].split(','):
                date, price, is_available = avail_data.split(' ')
                availability.append({
                    'date': date,
                    'price': float(price),
                    'is_available': bool(int(is_available))
                })
        stay['availability'] = availability
        
        # Clean up response
        del stay['image_data']
        del stay['availability_data']
        
        return jsonify(stay)
        
    except Exception as e:
        print("Error fetching host stay:", str(e))
        return jsonify({
            'message': 'Failed to fetch stay',
            'error': str(e)
        }), 500

@app.route('/api/listings/nearby', methods=['GET'])
def get_nearby_listings():
    try:
        lat = float(request.args.get('lat'))
        lng = float(request.args.get('lng'))
        radius = float(request.args.get('radius', 10))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query food experiences
        cursor.execute("""
            SELECT 
                id, 
                title,
                'food' as type,
                latitude,
                longitude,
                (6371 * acos(
                    cos(radians(%s)) * cos(radians(latitude)) *
                    cos(radians(longitude) - radians(%s)) +
                    sin(radians(%s)) * sin(radians(latitude))
                )) as distance
            FROM food_experiences
            WHERE status = 'published'
            HAVING distance <= %s
            ORDER BY distance
        """, (lat, lng, lat, radius))
        
        food_listings = cursor.fetchall()

        # Query stays with same parameters
        cursor.execute("""
            SELECT 
                id, 
                title,
                'stay' as type,
                latitude,
                longitude,
                (6371 * acos(
                    cos(radians(%s)) * cos(radians(latitude)) *
                    cos(radians(longitude) - radians(%s)) +
                    sin(radians(%s)) * sin(radians(latitude))
                )) as distance
            FROM stays
            WHERE status = 'published'
            HAVING distance <= %s
            ORDER BY distance
        """, (lat, lng, lat, radius))
        
        stay_listings = cursor.fetchall()

        return jsonify(food_listings + stay_listings)
    except Exception as e:
        print("Error fetching nearby listings:", str(e))
        return jsonify({'error': 'Failed to fetch nearby listings'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Make sure to create the directory structure:
# backend/
#   static/
#     images/
#       placeholder-food.jpg

@app.route('/api/host/food-experiences/<int:experience_id>/images', methods=['POST'])
@token_required
def upload_food_experience_images(current_user, experience_id):
    try:
        if 'images' not in request.files:
            return jsonify({'message': 'No images provided'}), 400
            
        files = request.files.getlist('images')
        uploaded_images = []
        
        for file in files:
            if file and allowed_file(file.filename):
                # Generate a secure filename without order numbers
                filename = secure_filename(file.filename)
                base, ext = os.path.splitext(filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                new_filename = f"{base}_{timestamp}{ext}"
                
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                file.save(file_path)
                
                # Save image info to database without order number
                conn = get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO food_experience_images 
                    (experience_id, image_path) 
                    VALUES (%s, %s)
                """, (experience_id, new_filename))
                
                conn.commit()
                uploaded_images.append(new_filename)
                
        return jsonify({
            'message': 'Images uploaded successfully',
            'images': uploaded_images
        })
        
    except Exception as e:
        print("Error uploading images:", str(e))
        return jsonify({
            'message': 'Failed to upload images',
            'error': str(e)
        }), 500
    

    

if __name__ == '__main__':
    app.run(debug=True) 
