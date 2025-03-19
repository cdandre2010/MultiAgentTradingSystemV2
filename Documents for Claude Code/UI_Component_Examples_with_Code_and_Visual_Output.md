# UI Component Examples with Code and Visual Output

This document provides code examples for key UI components that Claude Code can implement for the Trading Strategy System frontend, along with visual representations of how they'll appear when rendered.

## Table of Contents

1. [Theme Setup](#theme-setup)
2. [Layout Components](#layout-components)
3. [Conversation Interface](#conversation-interface)
4. [Chart Components](#chart-components)
5. [Strategy Builder Components](#strategy-builder-components)
6. [Form Components](#form-components)
7. [Utility Components](#utility-components)
8. [Page Examples](#page-examples)

## Theme Setup

First, create a custom theme that extends Chakra UI's default theme with our color palette, typography, and component styles.

```javascript
// src/theme.js
import { extendTheme } from '@chakra-ui/react';

const colors = {
  primary: {
    50: '#DBEAFE',
    100: '#BFDBFE',
    200: '#93C5FD',
    300: '#60A5FA',
    400: '#3B82F6',
    500: '#2563EB', // Primary Blue
    600: '#1E40AF', // Dark Blue
    700: '#1E3A8A',
    800: '#1E3A8A',
    900: '#172554',
  },
  success: {
    500: '#10B981', // Green
  },
  error: {
    500: '#EF4444', // Red
  },
  warning: {
    500: '#F59E0B', // Yellow
  },
  accent: {
    500: '#8B5CF6', // Purple
  },
  // Other theme colors...
};

// Other theme components...

const theme = extendTheme({
  colors,
  fonts,
  fontSizes,
  space,
  radii,
  components,
});

export default theme;
```

## Layout Components

### Main Layout

The main layout includes the sidebar navigation and top bar.

```javascript
// src/components/layout/MainLayout.jsx
import { Box, Flex } from '@chakra-ui/react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

function MainLayout({ children }) {
  return (
    <Flex h="100vh" overflow="hidden">
      {/* Sidebar */}
      <Sidebar />
      {/* Main Content Area */}
      <Flex flex="1" direction="column" overflowX="hidden">
        <TopBar />
        <Box flex="1" p="6" overflowY="auto">
          {children}
        </Box>
      </Flex>
    </Flex>
  );
}

export default MainLayout;
```

**Visual Output:**

### Sidebar Navigation

```javascript
// src/components/layout/Sidebar.jsx
import {
  Box,
  VStack,
  Icon,
  Text,
  Flex,
  Divider,
  Link
} from '@chakra-ui/react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import {
  MdDashboard,
  MdShowChart,
  MdAddCircle,
  MdCheckCircle,
  MdBarChart,
  MdSettings
} from 'react-icons/md';

// Component code...
```

**Visual Output:**

### Top Bar

```javascript
// src/components/layout/TopBar.jsx
import {
  Flex,
  IconButton,
  Avatar,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  MenuDivider,
  Text,
  HStack,
  Box,
  Button,
  useDisclosure,
  Icon,
  Badge
} from '@chakra-ui/react';
import {
  MdMenu,
  MdNotifications,
  MdHelp,
  MdPerson,
  MdExitToApp,
  MdSettings
} from 'react-icons/md';

// Component code...
```

**Visual Output:**

## Conversation Interface

### Conversation Container

```javascript
// src/components/conversation/ConversationContainer.jsx
import { Box, VStack, Flex, Button, Icon } from '@chakra-ui/react';
import { useState, useRef, useEffect } from 'react';
import { MdArrowDownward } from 'react-icons/md';
import MessageList from './MessageList';
import MessageInput from './MessageInput';

// Component code...
```

**Visual Output:**

### Message Components

```javascript
// src/components/conversation/UserMessage.jsx
import { Box, Text, Flex } from '@chakra-ui/react';

function UserMessage({ message }) {
  return (
    <Flex justify="flex-end">
      <Box
        maxW="70%"
        bg="primary.50"
        color="gray.800"
        p="3"
        borderRadius="12px 12px 0 12px"
      >
        <Text>{message.content}</Text>
        <Text fontSize="xs" color="gray.400" mt="1" textAlign="right">
          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </Text>
      </Box>
    </Flex>
  );
}

// Other message components...
```

**Visual Output:**

### Message Input

```javascript
// src/components/conversation/MessageInput.jsx
import {
  InputGroup,
  Input,
  InputRightElement,
  IconButton,
  useColorModeValue,
} from '@chakra-ui/react';
import { useState } from 'react';
import { MdSend } from 'react-icons/md';

// Component code...
```

**Visual Output:**

## Chart Components

### Equity Curve Chart

```javascript
// src/components/charts/EquityCurveChart.jsx
import { Box, useColorModeValue, Spinner, Center, Text } from '@chakra-ui/react';
import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Component code...
```

**Visual Output:**

### Performance Metrics Cards

```javascript
// src/components/charts/PerformanceMetrics.jsx
import { SimpleGrid, Stat, StatLabel, StatNumber, StatHelpText, StatArrow, Box, Text } from '@chakra-ui/react';

// Component code...
```

**Visual Output:**

### Candlestick Chart

```javascript
// src/components/charts/CandlestickChart.jsx
import { Box, useColorModeValue, Flex, Select, Spinner, Center, Text } from '@chakra-ui/react';
import { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Bar, BarChart } from 'recharts';

// Component code...
```

**Visual Output:**

## Strategy Builder Components

### Strategy Builder Container

```javascript
// src/components/strategy/StrategyBuilderContainer.jsx
import { Grid, GridItem, Box, Heading, Text } from '@chakra-ui/react';
import { useState } from 'react';
import ConversationContainer from '../conversation/ConversationContainer';
import StrategyVisualization from './StrategyVisualization';
import StrategyProgress from './StrategyProgress';

// Component code...
```

**Visual Output:**

### Strategy Progress

```javascript
// src/components/strategy/StrategyProgress.jsx
import { Box, Flex, useBreakpointValue, Circle, Text, Divider } from '@chakra-ui/react';
import { MdCheck } from 'react-icons/md';

// Component code...
```

**Visual Output:**

### Strategy Visualization

```javascript
// src/components/strategy/StrategyVisualization.jsx
import { Box, VStack, HStack, Text, Badge, Divider, Heading, List, ListItem, ListIcon } from '@chakra-ui/react';
import { MdCheckCircle, MdWarning } from 'react-icons/md';

// Component code...
```

**Visual Output:**

## Form Components

### Parameter Input

```javascript
// src/components/form/ParameterInput.jsx
import {
  FormControl,
  FormLabel,
  FormHelperText,
  FormErrorMessage,
  Input,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  HStack,
  Box
} from '@chakra-ui/react';

// Component code...
```

**Visual Output:**

### Indicator Selector

```javascript
// src/components/form/IndicatorSelector.jsx
import {
  Box,
  VStack,
  HStack,
  Button,
  Text,
  Heading,
  Divider,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  SimpleGrid,
  Flex,
  IconButton
} from '@chakra-ui/react';
import { useState, useEffect } from 'react';
import { MdAdd, MdEdit, MdDelete } from 'react-icons/md';
import ParameterInput from './ParameterInput';

// Component code...
```

**Visual Output:**

**Modal View:**

## Utility Components

### Dashboard Card

```javascript
// src/components/utils/DashboardCard.jsx
import { Box, Heading, Text, Flex, Icon, Divider } from '@chakra-ui/react';
import { MdTrendingUp, MdTrendingDown } from 'react-icons/md';

// Component code...
```

**Visual Output:**

### Empty State

```javascript
// src/components/utils/EmptyState.jsx
import { VStack, Text, Button, Icon, Box } from '@chakra-ui/react';

// Component code...
```

**Visual Output:**

### Loading Spinner

```javascript
// src/components/utils/LoadingSpinner.jsx
import { Flex, Spinner, Text, VStack } from '@chakra-ui/react';

// Component code...
```

**Visual Output:**

## Page Examples

### Dashboard Page

```javascript
// src/pages/DashboardPage.jsx
import { Box, SimpleGrid, Heading, Flex, Text, Button, Icon, Divider } from '@chakra-ui/react';
import { MdAddCircle, MdAttachMoney, MdInsights, MdShowChart, MdBarChart } from 'react-icons/md';
import MainLayout from '../components/layout/MainLayout';
import DashboardCard from '../components/utils/DashboardCard';
import EquityCurveChart from '../components/charts/EquityCurveChart';
import EmptyState from '../components/utils/EmptyState';
import { useNavigate } from 'react-router-dom';

// Component code...
```

**Visual Output:**

### Strategy Creation Page

```javascript
// src/pages/CreateStrategyPage.jsx
import { Box } from '@chakra-ui/react';
import MainLayout from '../components/layout/MainLayout';
import StrategyBuilderContainer from '../components/strategy/StrategyBuilderContainer';

function CreateStrategyPage() {
  return (
    <MainLayout>
      <StrategyBuilderContainer />
    </MainLayout>
  );
}

export default CreateStrategyPage;
```

**Visual Output:**

### Backtest Results Page

```javascript
// src/pages/BacktestResultsPage.jsx
import { Box, Heading, SimpleGrid, Button, Flex, Tab, TabList, TabPanel, TabPanels, Tabs } from '@chakra-ui/react';
import { MdDownload, MdSettings, MdPlayArrow } from 'react-icons/md';
import MainLayout from '../components/layout/MainLayout';
import EquityCurveChart from '../components/charts/EquityCurveChart';
import PerformanceMetrics from '../components/charts/PerformanceMetrics';

// Component code...
```

**Visual Output:**

## Interactive Components (Animated)

For key interactive components, here are descriptions of their animations and behaviors:

### Conversation Flow

- User messages appear from the right side with a subtle fade-in
- Agent messages appear from the left with a typing indicator first
- System messages fade in from the center
- New messages cause automatic scrolling to the bottom
- A "scroll to bottom" button appears when not at the bottom

### Strategy Builder Flow

- Progress steps highlight as the user advances
- Strategy visualization updates in real-time as conversation progresses
- Completed sections show check marks
- Incomplete sections show warning icons
- Parameter changes reflect immediately in the visualization

### Charts Interactions

- Tooltips appear on hover
- Zoom controls allow focusing on specific time periods
- Legend toggles show/hide data series
- Timeframe selectors update the chart with smooth transitions

These components create a cohesive, intuitive interface that guides users through the strategy creation process while providing immediate visual feedback and a conversational experience.

## Visual Output Demo

```javascript
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Sample data for charts
const equityData = [
  { date: '2023-01-01', equity: 10000 },
  { date: '2023-02-01', equity: 10500 },
  { date: '2023-03-01', equity: 11200 },
  { date: '2023-04-01', equity: 10800 },
  { date: '2023-05-01', equity: 11500 },
  { date: '2023-06-01', equity: 12200 },
  { date: '2023-07-01', equity: 13000 },
  { date: '2023-08-01', equity: 13800 },
  { date: '2023-09-01', equity: 13200 },
  { date: '2023-10-01', equity: 14000 },
  { date: '2023-11-01', equity: 15000 },
  { date: '2023-12-01', equity: 16000 }
];

// Icons
const ChartIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 3v18h18"></path>
    <path d="M18 12V8"></path>
    <path d="M14 8v4"></path>
    <path d="M10 16v-4"></path>
    <path d="M6 16v-4"></path>
  </svg>
);

const TrendUpIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline>
    <polyline points="16 7 22 7 22 13"></polyline>
  </svg>
);

const CheckIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"></polyline>
  </svg>
);

const WarningIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
    <line x1="12" y1="9" x2="12" y2="13"></line>
    <line x1="12" y1="17" x2="12.01" y2="17"></line>
  </svg>
);

// Conversation Message Components
const SystemMessage = ({ content }) => (
  <div className="flex justify-center mb-4">
    <div className="max-w-[80%] bg-gray-50 text-gray-600 p-2 rounded-md text-center">
      <p className="text-sm">{content}</p>
    </div>
  </div>
);

const AgentMessage = ({ content, agent = "M" }) => (
  <div className="flex mb-4">
    <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex justify-center items-center mr-2 mt-1 font-bold">
      {agent}
    </div>
    <div className="max-w-[70%] bg-white border border-gray-200 p-3 rounded-xl rounded-tl-none">
      <p>{content}</p>
      <p className="text-xs text-gray-400 mt-1">
        {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </p>
    </div>
  </div>
);

const UserMessage = ({ content }) => (
  <div className="flex justify-end mb-4">
    <div className="max-w-[70%] bg-blue-50 p-3 rounded-xl rounded-br-none">
      <p>{content}</p>
      <p className="text-xs text-gray-400 mt-1 text-right">
        {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </p>
    </div>
  </div>
);

const MessageInput = () => (
  <div className="relative">
    <input
      type="text"
      placeholder="Type your message..."
      className="w-full px-4 py-3 pr-12 border border-gray-200 rounded-full shadow-sm"
    />
    <button
      className="absolute right-2 bottom-2 w-8 h-8 bg-blue-600 text-white rounded-full flex justify-center items-center"
    >
      →
    </button>
  </div>
);

// Card component
const Card = ({ children, className = "" }) => (
  <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
    {children}
  </div>
);

// Main Component
const TradingSystemUI = () => {
  return (
    <div className="flex flex-col space-y-10 p-8">
      <h1 className="text-2xl font-bold text-center">Trading Strategy System UI Components</h1>

      {/* 1. Conversation Interface */}
      <div>
        <h2 className="text-xl font-bold mb-4">Conversation Interface</h2>
        <Card>
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold">Strategy Assistant</h3>
          </div>
          <div className="p-6">
            <div className="h-96 overflow-y-auto bg-gray-50 p-4 rounded-md mb-4">
              <SystemMessage content="Welcome to the Strategy Builder! Let's create a trading strategy together." />
              <AgentMessage content="Hi there! I'm your AI assistant. What type of trading strategy would you like to create today?" />
              <UserMessage content="I want to create a momentum strategy for Bitcoin." />
              <AgentMessage content="Great choice! Momentum strategies work well with volatile assets like Bitcoin. Let's start by defining the timeframe you want to trade on. Common options include 1-hour, 4-hour, or daily candles." />
              <UserMessage content="I'll go with the 4-hour timeframe." />
              <AgentMessage content="Perfect! The 4-hour timeframe is a good balance between capturing intraday moves and filtering out noise. Now, let's select indicators for your momentum strategy. Popular choices include RSI, MACD, and Moving Averages. Which indicators would you like to use?" />
            </div>
            <MessageInput />
          </div>
        </Card>
      </div>

      {/* 2. Strategy Builder */}
      <div>
        <h2 className="text-xl font-bold mb-4">Strategy Builder</h2>
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex justify-between items-center">
            {['Strategy Type', 'Instrument', 'Frequency', 'Indicators', 'Conditions', 'Risk'].map((step, i) => (
              <div key={i} className="flex items-center flex-1">
                <div className={`
                  w-10 h-10 rounded-full flex justify-center items-center font-bold
                  ${i < 2 ? 'bg-blue-600 text-white' : 
                    i === 2 ? 'bg-blue-100 text-blue-600' : 
                    'bg-gray-100 text-gray-400'}
                `}>
                  {i < 2 ? <CheckIcon /> : i + 1}
                </div>
                <span className={`
                  ml-2 text-sm font-medium hidden md:block
                  ${i === 2 ? 'text-blue-600 font-semibold' : 
                    i < 2 ? 'text-gray-800' : 
                    'text-gray-500'}
                `}>
                  {step}
                </span>
                {i < 5 && <div className={`flex-1 h-0.5 mx-2 ${i < 2 ? 'bg-blue-600' : 'bg-gray-200'}`} />}
              </div>
            ))}
          </div>
        </div>

        {/* Strategy Builder Grid */}
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Strategy Visualization Panel */}
          <Card className="lg:w-5/12">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold">Strategy Visualization</h3>
            </div>
            <div className="p-6">
              <div className="flex flex-col space-y-4">
                <div>
                  <h4 className="text-lg font-medium text-gray-800 mb-2">
                    BTC Momentum Strategy
                  </h4>
                  <span className="inline-block bg-blue-50 text-blue-600 px-2 py-1 rounded text-sm font-medium mb-2">
                    momentum
                  </span>
                </div>

                <hr className="border-gray-200" />

                <div className="flex justify-between">
                  <span className="font-medium">Instrument:</span>
                  <span>BTCUSDT</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Timeframe:</span>
                  <span>4h</span>
                </div>

                <hr className="border-gray-200" />

                <div>
                  <h4 className="text-sm font-semibold mb-2">Indicators</h4>
                  <p className="text-gray-400">No indicators added</p>
                </div>

                <hr className="border-gray-200" />

                <div>
                  <h4 className="text-sm font-semibold mb-2">Conditions</h4>
                  <p className="text-gray-400">No conditions defined</p>
                </div>

                <hr className="border-gray-200" />

                <div>
                  <h4 className="text-sm font-semibold mb-2">Risk Management</h4>
                  <p className="text-gray-400">Not configured</p>
                </div>

                <hr className="border-gray-200" />

                <div className="bg-gray-50 p-3 rounded-md">
                  <h4 className="text-sm font-semibold mb-2">Strategy Status</h4>
                  <div className="space-y-1">
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2"><CheckIcon /></span>
                      <span className="text-sm">Strategy Type</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-green-500 mr-2"><CheckIcon /></span>
                      <span className="text-sm">Instrument Selection</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-yellow-500 mr-2"><WarningIcon /></span>
                      <span className="text-sm">Frequency Selection</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-yellow-500 mr-2"><WarningIcon /></span>
                      <span className="text-sm">Indicators</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-yellow-500 mr-2"><WarningIcon /></span>
                      <span className="text-sm">Entry/Exit Conditions</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-yellow-500 mr-2"><WarningIcon /></span>
                      <span className="text-sm">Risk Management</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Conversation Panel */}
          <Card className="lg:w-7/12">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold">Conversation Assistant</h3>
            </div>
            <div className="p-6">
              <p className="text-gray-600 mb-4">
                I'll help you build your trading strategy step by step. Tell me what you'd like to create.
              </p>
              <div className="h-64 overflow-y-auto bg-gray-50 p-4 rounded-md mb-4">
                <SystemMessage content="Welcome to the Strategy Builder! Let's create a trading strategy together." />
                <AgentMessage content="Hi there! I'm your AI assistant. What type of trading strategy would you like to create today?" />
                <UserMessage content="I want to create a momentum strategy for Bitcoin." />
                <AgentMessage content="Great choice! Momentum strategies work well with volatile assets like Bitcoin. Let's start by defining the timeframe you want to trade on. Common options include 1-hour, 4-hour, or daily candles." />
                <UserMessage content="I'll go with the 4-hour timeframe." />

                {/* Typing indicator */}
                <div className="flex mb-4">
                  <div className="w-8 h-8 rounded-full bg-blue-600 text-white flex justify-center items-center mr-2 mt-1 font-bold">
                    M
                  </div>
                  <div className="max-w-[70%] bg-white border border-gray-200 p-3 rounded-xl rounded-tl-none">
                    <div className="flex items-center">
                      <div className="h-2 w-2 rounded-full bg-blue-600 mr-1 opacity-60 animate-pulse" />
                      <div className="h-2 w-2 rounded-full bg-blue-600 mr-1 opacity-60 animate-pulse" style={{ animationDelay: '0.2s' }} />
                      <div className="h-2 w-2 rounded-full bg-blue-600 opacity-60 animate-pulse" style={{ animationDelay: '0.4s' }} />
                    </div>
                  </div>
                </div>
              </div>
              <MessageInput />
            </div>
          </Card>
        </div>
      </div>

      {/* 3. Dashboard UI */}
      <div>
        <h2 className="text-xl font-bold mb-4">Dashboard</h2>
        
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-xl font-bold">Dashboard</h2>
            <p className="text-gray-600 mt-1">Welcome back, John!</p>
          </div>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-md flex items-center">
            <span className="mr-2">+</span>
            Create Strategy
          </button>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <div className="p-6 relative overflow-hidden">
              {/* Background Accent */}
              <div className="absolute top-0 right-0 bottom-0 w-1/3 bg-blue-50 opacity-50 rounded-l-full" />
              <div className="flex justify-between relative">
                <div>
                  <p className="text-gray-500 text-sm">Total Return</p>
                  <h3 className="text-2xl font-bold mt-1">+26.54%</h3>
                  <div className="flex items-center text-green-500 font-medium text-sm mt-1">
                    <span className="mr-1">↑</span>
                    3.2%
                  </div>
                </div>
                <div className="w-12 h-12 bg-blue-100 text-blue-700 rounded-lg flex justify-center items-center">
                  <ChartIcon />
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 bottom-0 w-1/3 bg-purple-50 opacity-50 rounded-l-full" />
              <div className="flex justify-between relative">
                <div>
                  <p className="text-gray-500 text-sm">Active Strategies</p>
                  <h3 className="text-2xl font-bold mt-1">2</h3>
                </div>
                <div className="w-12 h-12 bg-purple-100 text-purple-700 rounded-lg flex justify-center items-center">
                  <span>📊</span>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 bottom-0 w-1/3 bg-green-50 opacity-50 rounded-l-full" />
              <div className="flex justify-between relative">
                <div>
                  <p className="text-gray-500 text-sm">Win Rate</p>
                  <h3 className="text-2xl font-bold mt-1">62.5%</h3>
                  <div className="flex items-center text-green-500 font-medium text-sm mt-1">
                    <span className="mr-1">↑</span>
                    5.1%
                  </div>
                </div>
                <div className="w-12 h-12 bg-green-100 text-green-700 rounded-lg flex justify-center items-center">
                  <TrendUpIcon />
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 bottom-0 w-1/3 bg-blue-50 opacity-50 rounded-l-full" />
              <div className="flex justify-between relative">
                <div>
                  <p className="text-gray-500 text-sm">Total Trades</p>
                  <h3 className="text-2xl font-bold mt-1">48</h3>
                </div>
                <div className="w-12 h-12 bg-blue-100 text-blue-700 rounded-lg flex justify-center items-center">
                  <span>🔄</span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Portfolio Performance Chart */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4">Portfolio Performance</h3>
          <Card>
            <div className="p-6 h-64 lg:h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={equityData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    tickFormatter={(date) => new Date(date).toLocaleDateString(undefined, { month: 'short' })}
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    domain={[10000, 'dataMax + 1000']}
                    tickFormatter={(value) => `${value.toLocaleString()}`}
                  />
                  <Tooltip
                    formatter={(value) => [`${value.toLocaleString()}`, 'Equity']}
                    labelFormatter={(date) => new Date(date).toLocaleDateString()}
                  />
                  <Line
                    type="monotone"
                    dataKey="equity"
                    stroke="#2563EB"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        {/* Strategies */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Your Strategies</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="text-lg font-semibold">BTC Momentum Strategy</h4>
                    <p className="text-gray-600 text-sm mt-1">
                      BTCUSDT • momentum
                    </p>
                  </div>
                  <span className="bg-green-50 text-green-700 py-1 px-2 rounded-md text-sm font-semibold">
                    +24.5%
                  </span>
                </div>
                <hr className="border-gray-200 mb-4" />
                <button className="w-full py-2 border border-blue-600 text-blue-600 rounded-md font-medium">
                  View Details
                </button>
              </div>
            </Card>

            <Card>
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h4 className="text-lg font-semibold">ETH Mean Reversion</h4>
                    <p className="text-gray-600 text-sm mt-1">
                      ETHUSDT • mean reversion
                    </p>
                  </div>
                  <span className="bg-green-50 text-green-700 py-1 px-2 rounded-md text-sm font-semibold">
                    +18.2%
                  </span>
                </div>
                <hr className="border-gray-200 mb-4" />
                <button className="w-full py-2 border border-blue-600 text-blue-600 rounded-md font-medium">
                  View Details
                </button>
              </div>
            </Card>
          </div>
        </div>
      </div>

      <style jsx global>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 1; }
        }
        .animate-pulse {
          animation: pulse 1.5s infinite;
        }
      `}</style>
    </div>
  );
};

export default TradingSystemUI;