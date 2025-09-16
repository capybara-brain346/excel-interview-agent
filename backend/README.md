# Excel Interview Agent Backend

A comprehensive Node.js/TypeScript backend for conducting Excel skills interviews with real-time evaluation capabilities.

## Features

- **Production-ready architecture** with services, controllers, and routes
- **PostgreSQL database** with TypeORM entities and migrations
- **Comprehensive logging** with Winston (console + file rotation)
- **Advanced error handling** with custom error classes and middleware
- **Request validation** using Joi schemas
- **Rate limiting** and security headers
- **TypeScript** with strict configuration
- **TypeORM migrations** and seeding system
- **Comprehensive API** for interviews and sessions

## Project Structure

```
src/
├── config/          # Configuration files
├── controllers/     # Request handlers
├── entities/        # TypeORM entities
├── middleware/      # Express middleware
├── migrations/      # TypeORM migrations
├── routes/          # API routes
├── seeds/           # Database seed files
├── services/        # Business logic
├── test/            # Test setup
├── types/           # TypeScript type definitions
└── utils/           # Utility functions
```

## Prerequisites

- Node.js 18+
- PostgreSQL 12+
- npm or yarn

## Installation

1. Clone the repository
2. Install dependencies:

   ```bash
   npm install
   ```

3. Set up environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. Set up PostgreSQL database:

   ```bash
   createdb excel_interview_agent
   ```

5. Run TypeORM migrations:

   ```bash
   npm run db:migrate
   ```

6. Seed the database (optional):
   ```bash
   npm run db:seed
   ```

## Available Scripts

### Development

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build TypeScript to JavaScript
- `npm run build:watch` - Build with watch mode

### Database Operations

- `npm run db:migrate` - Run all pending TypeORM migrations
- `npm run db:rollback` - Rollback last migration
- `npm run db:generate` - Generate new migration from entity changes
- `npm run db:create` - Create new empty migration
- `npm run db:seed` - Run database seeds
- `npm run db:reset` - Rollback, migrate, and seed

### Production

- `npm start` - Start production server
- `npm run logs:clear` - Clear log files

### Code Quality

- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint issues
- `npm test` - Run tests

## API Endpoints

### Interviews

- `POST /api/interviews` - Create interview
- `GET /api/interviews` - List interviews (with pagination)
- `GET /api/interviews/:id` - Get interview details
- `PUT /api/interviews/:id` - Update interview
- `DELETE /api/interviews/:id` - Delete interview
- `POST /api/interviews/:id/questions` - Add question to interview
- `PUT /api/interviews/questions/:questionId` - Update question
- `DELETE /api/interviews/questions/:questionId` - Delete question

### Sessions

- `POST /api/sessions` - Create interview session
- `GET /api/sessions/:id` - Get session details
- `POST /api/sessions/:id/start` - Start session
- `POST /api/sessions/:id/responses` - Submit response
- `POST /api/sessions/:id/complete` - Complete session
- `POST /api/sessions/:id/abandon` - Abandon session
- `PUT /api/sessions/responses/:responseId/evaluate` - Evaluate response
- `GET /api/sessions/interview/:interviewId` - Get sessions by interview

### Health Check

- `GET /api/health` - Application health status

## Environment Variables

| Variable      | Description       | Default                 |
| ------------- | ----------------- | ----------------------- |
| `NODE_ENV`    | Environment       | `development`           |
| `PORT`        | Server port       | `3001`                  |
| `DB_HOST`     | Database host     | `localhost`             |
| `DB_PORT`     | Database port     | `5432`                  |
| `DB_NAME`     | Database name     | `excel_interview_agent` |
| `DB_USER`     | Database user     | `postgres`              |
| `DB_PASSWORD` | Database password | -                       |
| `LOG_LEVEL`   | Logging level     | `info`                  |
| `JWT_SECRET`  | JWT secret key    | -                       |
| `CORS_ORIGIN` | CORS origin       | `http://localhost:3000` |

## Database Schema

### Interviews

- Basic interview information (title, description, difficulty, duration)
- Status management (draft, active, archived)

### Interview Questions

- Question text and type (multiple choice, formula, practical)
- Excel scenarios with data setup and expected outputs
- Scoring and ordering

### Interview Sessions

- Candidate information and session tracking
- Status management (pending, in_progress, completed, abandoned)
- Total scoring

### Session Responses

- Individual question responses
- Time tracking and scoring
- Correctness evaluation

## Logging

The application uses Winston for comprehensive logging:

- **Console logging** with colors and formatting
- **File logging** with daily rotation
- **Structured logging** with request IDs and metadata
- **Error logging** with stack traces

Log files are stored in the `logs/` directory:

- `application-YYYY-MM-DD.log` - General application logs
- `error-YYYY-MM-DD.log` - Error logs only

## Error Handling

- **Custom error classes** for different error types
- **Async error handling** with proper middleware
- **Database error mapping** for common PostgreSQL errors
- **Request validation errors** with detailed messages
- **Production-safe error responses** (no stack traces in prod)

## Security Features

- **Helmet.js** for security headers
- **Rate limiting** to prevent abuse
- **CORS** configuration
- **Request size limits**
- **SQL injection protection** via TypeORM query builder
- **Input validation** on all endpoints

## Development

1. Start the development server:

   ```bash
   npm run dev
   ```

2. The server will start on `http://localhost:3001`

3. API documentation available at the root endpoint

4. Use tools like Postman or curl to test the endpoints

## Production Deployment

1. Build the application:

   ```bash
   npm run build
   ```

2. Set production environment variables

3. Run TypeORM migrations:

   ```bash
   npm run db:migrate
   ```

4. Start the server:
   ```bash
   npm start
   ```

## Testing

Run the test suite:

```bash
npm test
```

Tests include:

- Unit tests for services and utilities
- Integration tests for API endpoints
- Database operation tests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run linting and tests
6. Submit a pull request

## License

ISC License
