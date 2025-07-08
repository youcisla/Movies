# Django Movie Recommendation System

A modern, production-ready movie recommendation system built with Django, MongoDB Atlas, and Neo4j AuraDB.

## Project Overview

This system provides intelligent movie recommendations using:
- **MongoDB Atlas**: NoSQL document database for movies, reviews, and user data
- **Neo4j AuraDB**: Graph database for modeling user-movie relationships
- **TMDb API**: External API for fetching comprehensive movie data
- **Django**: Backend framework with REST API
- **Bootstrap**: Modern, responsive frontend UI

## Features

### Core Functionality
- Movie browsing and search
- User reviews and ratings
- Intelligent recommendation algorithms
- Admin dashboard for data management
- Real-time analytics and insights

### Recommendation Algorithms
1. **Content-Based Filtering**: Genre, director, cast similarity
2. **Graph-Based Recommendations**: User-movie relationship analysis
3. **Hybrid Approach**: Combines both methods for optimal results

### Analytics Dashboard
- Movie popularity trends
- Average ratings analysis
- Review sentiment insights
- User engagement metrics

## Project Structure

```
DjangoBot/
├── backend/                 # Django backend application
│   ├── movie_recommender/   # Main Django project
│   ├── movies/             # Movies app
│   ├── recommendations/    # Recommendation engine
│   ├── analytics/          # Analytics and insights
│   └── requirements.txt    # Python dependencies
├── frontend/               # Frontend templates and static files
│   ├── templates/         # Django templates
│   ├── static/           # CSS, JS, images
│   └── components/       # Reusable UI components
├── data/                  # Data processing and ETL
│   ├── etl_scripts/      # Data extraction and transformation
│   ├── notebooks/        # Jupyter notebooks for analysis
│   └── dumps/           # Database backup files
├── deployment/           # Deployment configurations
│   ├── heroku/          # Heroku deployment files
│   └── docker/          # Docker configurations
└── docs/                # Documentation
```

## Technology Stack

### Backend
- **Django 4.2+**: Web framework
- **pymongo**: MongoDB driver
- **py2neo**: Neo4j Python driver
- **requests**: HTTP library for TMDb API
- **django-cors-headers**: CORS support
- **django-rest-framework**: REST API

### Frontend
- **Bootstrap 5**: CSS framework
- **Chart.js**: Data visualization
- **jQuery**: DOM manipulation
- **Font Awesome**: Icons

### Databases
- **MongoDB Atlas**: Document database
- **Neo4j AuraDB**: Graph database

### External APIs
- **TMDb API**: Movie data source

### Deployment
- **Heroku**: Cloud platform
- **WhiteNoise**: Static file serving
- **Gunicorn**: WSGI server

## Prerequisites

- Python 3.8+
- MongoDB Atlas account
- Neo4j AuraDB account
- TMDb API key
- Heroku account (for deployment)

## Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd DjangoBot
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
```

### 3. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the backend directory:
```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB Atlas
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/moviedb?retryWrites=true&w=majority

# Neo4j AuraDB
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# TMDb API
TMDB_API_KEY=your-tmdb-api-key
TMDB_BASE_URL=https://api.themoviedb.org/3

# Heroku (for deployment)
HEROKU_APP_NAME=your-app-name
```

### 5. Database Setup
```bash
# Run ETL script to populate initial data
python manage.py migrate
python data/etl_scripts/populate_movies.py
python data/etl_scripts/setup_neo4j.py
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
```

### 7. Run Development Server
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## API Endpoints

### Movies
- `GET /api/movies/` - List all movies
- `GET /api/movies/{id}/` - Get movie details
- `POST /api/movies/` - Create new movie (admin)
- `PUT /api/movies/{id}/` - Update movie (admin)
- `DELETE /api/movies/{id}/` - Delete movie (admin)

### Reviews
- `GET /api/reviews/` - List all reviews
- `POST /api/reviews/` - Create new review
- `GET /api/movies/{id}/reviews/` - Get movie reviews

### Recommendations
- `GET /api/recommendations/` - Get personalized recommendations
- `GET /api/recommendations/similar/{movie_id}/` - Get similar movies
- `GET /api/recommendations/trending/` - Get trending movies

### Analytics
- `GET /api/analytics/popularity/` - Movie popularity stats
- `GET /api/analytics/ratings/` - Rating distribution
- `GET /api/analytics/trends/` - Movie trends

## Frontend Features

### User Interface
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Modern UI**: Clean, intuitive Bootstrap-based design
- **Interactive Components**: Dynamic movie cards, rating systems
- **Search & Filter**: Advanced movie search with multiple filters

### Pages
- **Home**: Featured movies and recommendations
- **Movies**: Browse all movies with pagination
- **Movie Detail**: Detailed movie information and reviews
- **Recommendations**: Personalized movie suggestions
- **Analytics**: Dashboard with charts and insights
- **Admin**: Data management interface

## Data Processing

### ETL Pipeline
1. **Extract**: Fetch movie data from TMDb API
2. **Transform**: Clean and normalize data
3. **Load**: Store in MongoDB and create Neo4j relationships

### Data Models
```python
# MongoDB Models
class Movie:
    title, genre, director, cast, plot, ratings, etc.

class Review:
    user, movie, rating, comment, timestamp

class User:
    username, email, preferences, watch_history

# Neo4j Relationships
(User)-[:LIKES]->(Movie)
(User)-[:RATED]->(Movie)
(Movie)-[:SIMILAR_TO]->(Movie)
(Movie)-[:BELONGS_TO]->(Genre)
```

## Analytics & Insights

### MongoDB Aggregations
- Top-rated movies by genre
- User engagement metrics
- Review sentiment analysis
- Seasonal movie trends

### Neo4j Graph Queries
- User similarity analysis
- Movie recommendation paths
- Community detection
- Centrality measures

## Deployment

### Heroku Deployment
1. **Prepare for Deployment**
   ```bash
   # Install Heroku CLI
   heroku login
   heroku create your-app-name
   ```

2. **Configure Environment Variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set MONGODB_URI=your-mongodb-uri
   heroku config:set NEO4J_URI=your-neo4j-uri
   # ... other variables
   ```

3. **Deploy**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

4. **Initialize Database**
   ```bash
   heroku run python manage.py migrate
   heroku run python data/etl_scripts/populate_movies.py
   ```

## Project Management

### Trello Board
[Link to Trello Board](https://trello.com/b/your-board-id)

**Board Structure:**
- **Backlog**: Future features and improvements
- **To Do**: Current sprint tasks
- **In Progress**: Active development
- **Review**: Code review and testing
- **Done**: Completed features

### Task Categories
- Backend Development
- Frontend Development
- Data Processing
- Testing
- Deployment
- Documentation

## Presentation

### Google Slides
[Link to Presentation](https://docs.google.com/presentation/d/your-presentation-id)

**Slide Topics:**
1. Project Overview
2. Technical Architecture
3. Database Design
4. Recommendation Algorithms
5. User Interface
6. Analytics Dashboard
7. Deployment Strategy
8. Future Enhancements

## Data Exploration

### Jupyter Notebooks
Located in `data/notebooks/`:
- `01_data_exploration.ipynb`: Initial data analysis
- `02_recommendation_algorithms.ipynb`: Algorithm development
- `03_analytics_insights.ipynb`: Statistical analysis
- `04_performance_optimization.ipynb`: System optimization

## Testing

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test movies
python manage.py test recommendations

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Categories
- **Unit Tests**: Individual function testing
- **Integration Tests**: Component interaction testing
- **API Tests**: REST endpoint testing
- **Database Tests**: Data integrity testing

## Troubleshooting

### Common Issues
1. **MongoDB Connection**: Check URI and network access
2. **Neo4j Authentication**: Verify credentials and URI
3. **TMDb API**: Check API key and rate limits
4. **Static Files**: Run `collectstatic` for production

### Debug Mode
Enable debug mode for development:
```python
# settings.py
DEBUG = True
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Acknowledgments

- TMDb for movie data
- MongoDB and Neo4j for database services
- Django community for the excellent framework
- Bootstrap team for the UI framework

---

**Live Demo**: [https://your-app-name.herokuapp.com](https://your-app-name.herokuapp.com)

**Author**: Y.CHEHBOUB  
**Date**: July 2025  
**Version**: 1.0.0
