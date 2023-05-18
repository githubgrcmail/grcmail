//+------------------------------------------------------------------+
//|                                                      SMT.mq5     |
//|                                              Geilson Santana     |
//|                                               @geilson_minas     |
//+------------------------------------------------------------------+
#property copyright "Geilson Santana"
#property link      "@geilson_minas"
#property version   "1.00"
#property strict

// Parâmetros de entrada
input string Symbol1 = "EURUSD#";
input string Symbol2 = "USDX.a";
input ENUM_TIMEFRAMES TimeFrame1 = PERIOD_M5;
input ENUM_TIMEFRAMES TimeFrame2 = PERIOD_M15;
input ENUM_TIMEFRAMES TimeFrame3 = PERIOD_M30;
input bool isTimeFrame1Active = true; // Ativa/desativa o timeframe 1
input bool isTimeFrame2Active = true; // Ativa/desativa o timeframe 2
input bool isTimeFrame3Active = true; // Ativa/desativa o timeframe 3
input int Periods = 14;
input double CorrelationThreshold = -98;


//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {

  }

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
    // Aqui verificamos cada booleana para desenhar suporte e resistência para cada timeframe
    if(isTimeFrame1Active)
    {
        DrawSupportAndResistance(Symbol1, TimeFrame1);
        DrawSupportAndResistance(Symbol2, TimeFrame1);
    }
    if(isTimeFrame2Active)
    {
        DrawSupportAndResistance(Symbol1, TimeFrame2);
        DrawSupportAndResistance(Symbol2, TimeFrame2);
    }
    if(isTimeFrame3Active)
    {
        DrawSupportAndResistance(Symbol1, TimeFrame3);
        DrawSupportAndResistance(Symbol2, TimeFrame3);
    }

    // Calcular a correlação e a variação de preço para cada timeframe
    double Correlation1, Correlation2, Correlation3;
    double change1_symbol1, change1_symbol2, change2_symbol1, change2_symbol2, change3_symbol1, change3_symbol2;

    if(isTimeFrame1Active)
    {
        Correlation1 = CalculateCorrelation(Symbol1, Symbol2, TimeFrame1, Periods);
        change1_symbol1 = iClose(Symbol1, TimeFrame1, 0) - iClose(Symbol1, TimeFrame1, 1);
        change1_symbol2 = iClose(Symbol2, TimeFrame1, 0) - iClose(Symbol2, TimeFrame1, 1);
    }

    if(isTimeFrame2Active)
    {
        Correlation2 = CalculateCorrelation(Symbol1, Symbol2, TimeFrame2, Periods);
        change2_symbol1 = iClose(Symbol1, TimeFrame2, 0) - iClose(Symbol1, TimeFrame2, 1);
        change2_symbol2 = iClose(Symbol2, TimeFrame2, 0) - iClose(Symbol2, TimeFrame2, 1);
    }

    if(isTimeFrame3Active)
    {
        Correlation3 = CalculateCorrelation(Symbol1, Symbol2, TimeFrame3, Periods);
        change3_symbol1 = iClose(Symbol1, TimeFrame3, 0) - iClose(Symbol1, TimeFrame3, 1);
        change3_symbol2 = iClose(Symbol2, TimeFrame3, 0) - iClose(Symbol2, TimeFrame3, 1);
    }

    // Verificar se há divergências em todos os timeframes ativos
    bool isDivergenceDetected = false;

    if(isTimeFrame1Active && Correlation1 * 100 <= CorrelationThreshold && change1_symbol1 * change1_symbol2 > 0)
        isDivergenceDetected = true;
    if(isTimeFrame2Active && Correlation2 * 100 <= CorrelationThreshold && change2_symbol1 * change2_symbol2 > 0)
        isDivergenceDetected = true;
    if(isTimeFrame3Active && Correlation3 * 100 <= CorrelationThreshold && change3_symbol1 * change3_symbol2 > 0)
        isDivergenceDetected = true;
    
    if (isDivergenceDetected)
    {
        Print("Divergência detectada em um dos timeframes ativos para ", Symbol1, " e ", Symbol2);
        
        // Adicione sua lógica para agir sobre o sinal SMT aqui
        
        if(isTimeFrame1Active)
        {
            DrawFibo(Symbol1, TimeFrame1);
            DrawFibo(Symbol2, TimeFrame1);
        }
        if(isTimeFrame2Active)
        {
            DrawFibo(Symbol1, TimeFrame2);
            DrawFibo(Symbol2, TimeFrame2);
        }
        if(isTimeFrame3Active)
        {
            DrawFibo(Symbol1, TimeFrame3);
            DrawFibo(Symbol2, TimeFrame3);
        }
    }
  }

// (O resto do seu código permanece inalterado)


double CalculateCorrelation(string symbol1, string symbol2, ENUM_TIMEFRAMES timeframe, int periods)
{
    double price1[];
    double price2[];
    
    CopyClose(symbol1, timeframe, 0, periods, price1);
    CopyClose(symbol2, timeframe, 0, periods, price2);
    
    double mean1 = MathMean(price1);
    double mean2 = MathMean(price2);
    
    double variance1 = MathVariance(price1, mean1);
    double variance2 = MathVariance(price2, mean2);
    
    double covariance = MathCovariance(price1, price2, mean1, mean2);
    
    double correlation = covariance / MathSqrt(variance1 * variance2);
    
    return correlation;
}

double MathMean(double& array[])
{
    int len = ArraySize(array);
    double sum = 0;
    for(int i=0; i<len; i++)
    {
        sum += array[i];
    }
    return sum/len;
}

double MathVariance(double& array[], double mean)
{
    int len = ArraySize(array);
    double sum = 0;
    
    for(int i=0; i<len; i++)
    {
        sum += MathPow(array[i] - mean, 2);
    }
    return sum/len;
}

double MathCovariance(double& array1[], double& array2[], double mean1, double mean2)
{
    int len = ArraySize(array1);
    double sum = 0;
    
    for(int i=0; i<len; i++)
    {
        sum += (array1[i] - mean1) * (array2[i] - mean2);
    }
    return sum/len;
}

//+------------------------------------------------------------------+

void DrawSupportAndResistance(string symbol, ENUM_TIMEFRAMES timeframe)
{
    MqlRates rates[];
    int copied = CopyRates(symbol, timeframe, 0, 14, rates);
    
    if(copied > 0)
    {
        double highestHigh = rates[0].high;
        double lowestLow = rates[0].low;
        datetime highestHighTime = rates[0].time;
        datetime lowestLowTime = rates[0].time;
        
        for(int i=0; i<copied; i++)
        {
            if(rates[i].high > highestHigh)
            {
                highestHigh = rates[i].high;
                highestHighTime = rates[i].time;
            }
            
            if(rates[i].low < lowestLow)
            {
                lowestLow = rates[i].low;
                lowestLowTime = rates[i].time;
            }
        }
        
        string resistanceLineName = symbol + "_resistance";
        string supportLineName = symbol + "_support";
        
        ObjectCreate(0, resistanceLineName, OBJ_HLINE, 0, 0, highestHigh);
        ObjectCreate(0, supportLineName, OBJ_HLINE, 0, 0, lowestLow);
        
        ObjectSetInteger(0, resistanceLineName, OBJPROP_COLOR, clrRed);
        ObjectSetInteger(0, supportLineName, OBJPROP_COLOR, clrGreen);
    }
    else
    {
        Print("Error copying rates. Error code: ", GetLastError());
    }
}

void DrawFibo(string symbol, ENUM_TIMEFRAMES timeframe)
{
    MqlRates rates[];
    int copied = CopyRates(symbol, timeframe, 0, 14, rates);

    if(copied > 0)
    {
        double highestHigh = rates[0].high;
        double lowestLow = rates[0].low;
        datetime highestHighTime = rates[0].time;
        datetime lowestLowTime = rates[0].time;

        for(int i=0; i<copied; i++)
        {
            if(rates[i].high > highestHigh)
            {
                highestHigh = rates[i].high;
                highestHighTime = rates[i].time;
            }
            
            if(rates[i].low < lowestLow)
            {
                lowestLow = rates[i].low;
                lowestLowTime = rates[i].time;
            }
        }
        
        string fiboName = symbol + "_fibo";

        if(highestHighTime > lowestLowTime) // if the high is more recent
        {
            if(ObjectCreate(0, fiboName, OBJ_FIBO, 0, lowestLowTime, lowestLow, highestHighTime, highestHigh))
            {
                for(int i = 0; i < 23; i++)
                {
                    ObjectSetInteger(0, fiboName, OBJPROP_LEVELCOLOR, i, clrWhite);
                }
            }
            else
            {
                Print("Erro ao criar o objeto Fibonacci. Código do erro: ", GetLastError());
            }
        }
        else // if the low is more recent
        {
            if(ObjectCreate(0, fiboName, OBJ_FIBO, 0, highestHighTime, highestHigh, lowestLowTime, lowestLow))
            {
                for(int i = 0; i < 23; i++)
                {
                    ObjectSetInteger(0, fiboName, OBJPROP_LEVELCOLOR, i, clrWhite);
                }
            }
            else
            {
                Print("Erro ao criar o objeto Fibonacci. Código do erro: ", GetLastError());
            }
        }

        // Calculate and print Fibonacci levels
        double high = highestHigh;
        double low = lowestLow;
        double levelPrices[6];
         
        levelPrices[0] = low; // 0% level 
        levelPrices[1] = high - 0.236 * (high - low); // 23.6% level
        levelPrices[2] = high - 0.382 * (high - low); // 38.2% level
        levelPrices[3] = high - 0.500 * (high - low); // 50% level
        levelPrices[4] = high - 0.618 * (high - low); // 61.8% level
        levelPrices[5] = high; // 0% level

        for(int i = 0; i < 6; i++)
        {
            Print("Fibonacci level ", i, " price: ", levelPrices[i]);
        }
    }
    else
    {
        Print("Erro ao copiar as taxas. Código do erro: ", GetLastError());
    }
}
