//+------------------------------------------------------------------+
//|                                           entradaautomatica2.mq5 |
//|                                                  Geilson Santana |
//|                                                   @geilson_minas |
//+------------------------------------------------------------------+
#property copyright "Geilson Santana"
#property link      "@geilson_minas"
#property version   "1.00"
#include <StdLibErr.mqh>

#include <Trade\SymbolInfo.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\OrderInfo.mqh>
#include <Trade\Trade.mqh>

#resource "\\Files\\Sounds\\alert.wav";


CSymbolInfo Symbol1;
CPositionInfo m_position;
CPositionInfo m_positionAtual;
CTrade m_trade;
COrderInfo m_order; 


input group  "◼ Identificador do Robô"; 
sinput string in_name = "B3";                   // --- Nome do expert
sinput ulong iMagic = 133;                      // --- Magic Number

input group  "◼ Parâmetros de Entrada"; 
input double iEntradaBuy = 1;                 // --- Entrada Buy
input double iEntradaSel = 1;                 // --- Entrada Sel
input double iGlobalStop = 150;                  // --- Stop
input double iGlobalTake = 200;                 // --- Take

input group "◼ Controle";
input bool iBuy = true;                         // --- Nova Entrada Buy
input bool iSel = true;                         // --- Nova Entrada Sel
input int iRebaixoMax = 600;                    // --- Rebaixamento Máximo
input string TradingStartTime = "09:00";        // --- Start Time
input string TradingEndTime = "13:00";          // --- End Time

input group  "◼ Parâmetros do Indicador"; 
input ENUM_TIMEFRAMES TimeFrame1 = PERIOD_M1;   // --- Timeframe 1 selecionável
input int CCI_Period1 = 30;                     // --- Período CCI 1 editável
input ENUM_TIMEFRAMES TimeFrame2 = PERIOD_M5;   // --- Timeframe 2 selecionável
input int CCI_Period2 = 14;                     // --- Período CCI 2 editável
input int iAmplitude = 2;                       // --- Amplitude

input group "◼ Painel";
input bool iPainel = true;                      // --- Exibir Painel
input color iColor = C'73,69,63';               // --- Cor Painel    
input color iColor2 = C'63,75,61';              // --- Cor2 Painel    
input color iColor3 = clrTan;                   // --- Cor3 Painel    
input ENUM_BASE_CORNER iPosition = CORNER_RIGHT_UPPER;   // --- Posição Painel
input int iMarginX = 3;                         // --- Margem Horizontal  
input int iMarginY = 3;                         // --- Margem Vertical



// Indicadores
int B3_Handle;
int FX_Handle1;
int FX_Handle2;

// Variáveis globais
double buyBuffer[];
bool buyBufferSeta = false;
double selBuffer[];
bool selBufferSeta = false;

double FX_Value1[];
double FX_Value2[];

//Buy
int abertasBuy = 0;
int abertasBuyPositivas = 0;
double profitBuy = 0.0;
double profitBuyPositivo = 0.0;
double volumeBuy = 0.0;
double volumeBuyPositivo = 0.0;

//Sel
int abertasSel = 0;
int abertasSelPositivas = 0;
double profitSel = 0.0;
double profitSelPositivo = 0.0;
double volumeSel = 0.0;
double volumeSelPositivo = 0.0;

double totalProfit = 0.0;
double acumulado = 0.0;
double acumuladoMaximo = 0.0;
double rebaixamento = 0.0;
double rebaixamentoMaximo = 0.0;

double minVolume;
double maxVolume;
double stepVolume;

int los = 0;
int win = 0;
int atualDay = 0;

int y;
int x;
long O = 0; //Objetos
string infos[] = {  
    "Positivo", 
    "Profit", 
    "Ordens", 
    "FluxoM5", 
    "FluxoM1", 
    "B3", 
    "B3Value", 
};
string objs[] = {  
    "Máxima",
    "Média",
    "Mínima",
    "BG",
    "BGTitulo",
    "Titulo",
    "Par",
    "BGTotal",
    "Total",
    "TotalValor",
    "RbBG",
    "RbL",
    "RbV",
    "RbBT",
    "RbBTM",
    "RbBTA",
    "sep",
    "AcBG",
    "AcL",
    "AcV",
    "AcBT",
    "AcBTM",
    "AcBTA",
        };

bool Painel;
bool InTest = false;
datetime inicio = TimeCurrent()-(GetTickCount64()/1000);
datetime lastCandleTime  = TimeCurrent();

datetime currentTime;
MqlDateTime mqlTime;

void OnDeinit(const int reason){
    IndicatorRelease(B3_Handle);
    IndicatorRelease(FX_Handle1);
    IndicatorRelease(FX_Handle2);

    //--- Remover o painel do gráfico
    RemovePanel();
    Comment("");
};
void OnTesterInit(){
    InTest = true;
};
void OnTesterDeinit(){};

int OnInit(){
    if (!Init()) return INIT_FAILED;
    if (!CheckInputs()) return INIT_PARAMETERS_INCORRECT;
    return (INIT_SUCCEEDED);
}

bool Init() {
    Symbol1.Name(Symbol());
    m_trade.SetExpertMagicNumber(iMagic);
    m_trade.SetMarginMode();
    m_trade.SetAsyncMode(true);
    m_trade.SetTypeFillingBySymbol(Symbol());
    m_trade.LogLevel(LOG_LEVEL_NO);

    Symbol1.Refresh();
    Symbol1.RefreshRates();
    
    m_trade.SetDeviationInPoints(5);

    if (!InitIndicators()) return false;

    minVolume = Symbol1.LotsMin();
    maxVolume = Symbol1.LotsMax();
    stepVolume = Symbol1.LotsStep();

    if(!InTest && iPainel) {RemovePanel();
    InitPanel();}
    return true;
}

bool CheckInputs(){
    //-- Inicio da verificação do Magic Number
    if (iMagic < 0){
        Print("Número Mágico deve ser maior que zero!");
        return false;
    }
    //-- Inicio da verificação do tamanho do lote
    if (!CheckVolumeValue(iEntradaBuy)){
        Print("Erro: Volume de entrada Buy.!");
        return false;
    }
     //-- Inicio da verificação do tamanho do lote
    if (!CheckVolumeValue(iEntradaSel)){
        Print("Erro: Volume de entrada Sell.!");
        return false;
    }
    return true;
}

bool InitIndicators(){
    // Configurando os buffers das setas
    ArraySetAsSeries(buyBuffer, true);
    ArraySetAsSeries(selBuffer, true);
    ArraySetAsSeries(FX_Value1, true);
    ArraySetAsSeries(FX_Value2, true);
    
    //SetIndexBuffer(0, buyBuffer);
    //SetIndexBuffer(1, selBuffer);


    // Obter o identificador do indicador para TimeFrame1 e CCI_Period1
    FX_Handle1 = iCustom(Symbol(), TimeFrame1, "FX.ex5", CCI_Period1);
    if (FX_Handle1 == INVALID_HANDLE)    {
        Print("Erro ao obter o identificador do indicador FX.ex5 para TimeFrame1 e CCI_Period1", GetLastError());
        return false;
    }

    // Obter o identificador do indicador para TimeFrame2 e CCI_Period2
    FX_Handle2 = iCustom(Symbol(), TimeFrame2, "FX.ex5", CCI_Period2);
    if (FX_Handle2 == INVALID_HANDLE)    {
        Print("Erro ao obter o identificador do indicador FX.ex5 para TimeFrame2 e CCI_Period2", GetLastError());
        return false;
    }
    
    // Inicializando o indicador personalizado
    B3_Handle = iCustom(Symbol(), TimeFrame1, "B3.ex5",iAmplitude);
    if (B3_Handle == INVALID_HANDLE) {
        Print("Erro ao inicializar o indicador: ", GetLastError());
        return false;
    }
    return true;
}

bool LoadIndicators(){
    // Obter o valor do indicador para a vela anterior em TimeFrame1 e CCI_Period1
    if (CopyBuffer(FX_Handle1, 0, 1, 1, FX_Value1) != 1) {
        Print("Erro ao obter o valor do indicador FX.ex5 para a vela anterior em TimeFrame1 e CCI_Period1", GetLastError());
        return false;
    }
    // Obter o valor do indicador para a vela anterior em TimeFrame2 e CCI_Period2
    if (CopyBuffer(FX_Handle2, 0, 0, 1, FX_Value2) != 1) {
        Print("Erro ao obter o valor do indicador FX.ex5 para a vela anterior em TimeFrame2 e CCI_Period2", GetLastError());
        return false;
    } 
    CopyBuffer(B3_Handle, 5, 1, 1, buyBuffer);
    if (buyBuffer[0]<500000) {
        buyBufferSeta = true;
    }else{
        buyBufferSeta = false;
    }
    CopyBuffer(B3_Handle, 6, 1, 1, selBuffer);
    if (selBuffer[0]<500000) {
        selBufferSeta = true;
    }else{
        selBufferSeta = false;
    }
    return true;
}

void OnTick() {
    Symbol1.Refresh();   
    //Verifica se o mercado está aberto
    if(Symbol1.TradeMode() == SYMBOL_TRADE_MODE_DISABLED) return;
    if (Symbol1.Ask() == 0 || Symbol1.Bid() == 0) return;
    Symbol1.RefreshRates();
    if (!LoadIndicators()) return;
    
    // Verificar se uma nova vela começou
    bool isNewCandle = CheckNewCandle();  
    
    if (isNewCandle){
        currentTime = TimeCurrent();
        TimeToStruct(currentTime, mqlTime);
        if(mqlTime.day!=atualDay){
            los = 0;
            win = 0;
            atualDay = mqlTime.day;
        }

        GetOpens();
        if(!InTest){
            if(iPainel && !Painel){
                Painel = true;
                RemovePanel();
                InitPanel();
            } 
            if(Painel && !iPainel) RemovePanel();
            if(Painel){
                Sinais();
                RedrawPanel();
                totalProfit = BotResult(inicio);
            } 
        }
        if(los>1 || win>1) return;
        // Verificando se há uma nova seta de compra ou venda na vela anterior e se uma nova vela começou
        if (PositionsTotal() == 0 && IsTradingTime(TradingStartTime, TradingEndTime)) {
            if (buyBufferSeta && FX_Value1[0] > 0 && FX_Value2[0] > 0) {
                OpenBuy(Symbol1, iEntradaBuy, iGlobalStop, iGlobalTake);
            } else if (selBufferSeta && FX_Value1[0] < 0 && FX_Value2[0] < 0) {
                OpenSel(Symbol1, iEntradaSel, iGlobalStop, iGlobalTake);
            }
        }
        
    }
}

void Sinais(){

    string indicador = "-";
    
    if(buyBufferSeta){
        PlaySound("\\Files\\Sounds\\alert.wav");
        ObjectSetString(0, "B3ValueV1", OBJPROP_TEXT, DoubleToString(buyBuffer[0],2));
    }else{
        ObjectSetString(0, "B3ValueV1", OBJPROP_TEXT, indicador);
    }
    if(selBufferSeta){
        PlaySound("\\Files\\Sounds\\alert.wav");
        ObjectSetString(0, "B3ValueV2", OBJPROP_TEXT, DoubleToString(selBuffer[0],2));
    }else{
        ObjectSetString(0, "B3ValueV2", OBJPROP_TEXT, indicador);
    }

    if (buyBufferSeta) indicador = "UP";
    ObjectSetString(0, "B3V1", OBJPROP_TEXT, indicador);
    
    indicador = "-";
    if (selBufferSeta) indicador = "DW";
    ObjectSetString(0, "B3V2", OBJPROP_TEXT, indicador);
    
    indicador = "-";
    if (FX_Value1[0] > 0) indicador = "UP";
    ObjectSetString(0, "FluxoM1V1", OBJPROP_TEXT, indicador);
    
    indicador = "-";
    if (FX_Value1[0] < 0) indicador = "DW";
    ObjectSetString(0, "FluxoM1V2", OBJPROP_TEXT, indicador);
    
    indicador = "-";
    if (FX_Value2[0] > 0) indicador = "UP";
    ObjectSetString(0, "FluxoM5V1", OBJPROP_TEXT, indicador);
    
    indicador = "-";
    if (FX_Value2[0] < 0) indicador = "DW";
    ObjectSetString(0, "FluxoM5V2", OBJPROP_TEXT, indicador);
                
}

void OnTradeTransaction(const MqlTradeTransaction& trans,const MqlTradeRequest& request,const MqlTradeResult& result){
    if(trans.type!=TRADE_TRANSACTION_DEAL_ADD)return;
    if(!HistoryDealSelect(trans.deal))return;
    if(HistoryDealGetInteger(trans.deal,DEAL_MAGIC)!=iMagic)return;
    if(HistoryDealGetInteger(trans.deal,DEAL_ENTRY)!=DEAL_ENTRY_OUT)return;
    if(HistoryDealGetString(trans.deal,DEAL_SYMBOL)!=_Symbol)return;
    long reason=HistoryDealGetInteger(trans.deal,DEAL_REASON);
    if(reason==DEAL_REASON_SL){
        los++;
    }else if(reason==DEAL_REASON_TP){
        win++;
    }
}

void GetOpens(){
    // Essa funcao atualiza os totalizadores apenas.   
    //Buy
    abertasBuy = 0;
    abertasBuyPositivas = 0;
    profitBuy = 0.0;
    profitBuyPositivo = 0.0;    
    volumeBuy = 0.0;
    volumeBuyPositivo = 0.0;    

    //Sel
    abertasSel = 0;
    abertasSelPositivas = 0;
    profitSel = 0.0;
    profitSelPositivo = 0.0;
    volumeSel = 0.0;
    volumeSelPositivo = 0.0;

    // Busca dos dados de compradas, profit e volume
    int total = PositionsTotal();
    if (total != 0) {
        //for (int i = total - 1; i >= 0; i--) {
        for (int i = 0; i < total; i++){
            m_position.SelectByIndex(i);
            if (m_position.Magic() != iMagic)continue;
            //if (m_position.Symbol() != Symbol1.Name())continue;

            double price = m_position.PriceOpen();
            double profit = m_position.Profit() + m_position.Commission() + m_position.Swap();
            double volume = m_position.Volume();
            
            if (m_position.PositionType() == POSITION_TYPE_BUY){
                abertasBuy++;

                if(profit > 0){
                    abertasBuyPositivas++;
                    profitBuyPositivo += profit;
                    volumeBuyPositivo += volume;
                }
                profitBuy += profit;
                volumeBuy += volume;
            }
            if (m_position.PositionType() == POSITION_TYPE_SELL){
                abertasSel++;
                if(profit > 0){
                    abertasSelPositivas++;
                    profitSelPositivo += profit;
                    volumeSelPositivo += volume;
                }
                profitSel += profit;
                volumeSel += volume;

            }
        }
    }

    rebaixamento = profitBuy+profitSel;
    if(rebaixamento>0) rebaixamento = 0;
    rebaixamento = MathAbs(rebaixamento);
    if(rebaixamento>rebaixamentoMaximo) rebaixamentoMaximo=rebaixamento;

    if(Painel) {
        if(rebaixamento<iRebaixoMax/4){
            ObjectSetInteger(0,"RbBTA", OBJPROP_BGCOLOR, clrGreen);
        }else if(rebaixamento<iRebaixoMax/3){
            ObjectSetInteger(0,"RbBTA", OBJPROP_BGCOLOR, clrGold);
        }else if(rebaixamento<iRebaixoMax/2){
            ObjectSetInteger(0,"RbBTA", OBJPROP_BGCOLOR, clrOrangeRed);
        }else{
            ObjectSetInteger(0,"RbBTA", OBJPROP_BGCOLOR, clrCrimson);
        }


        ObjectSetString(0, "RbV", OBJPROP_TEXT, "$ "+DoubleToString(rebaixamento, 2) + " | $ "+DoubleToString(rebaixamentoMaximo, 2));
        ObjectSetInteger(0,"RbBTM", OBJPROP_XSIZE, Porcento(iRebaixoMax, rebaixamentoMaximo)*360);
        ObjectSetInteger(0,"RbBTA", OBJPROP_XSIZE, Porcento(iRebaixoMax, rebaixamento)*360);

        ObjectSetString(0, "OrdensV1", OBJPROP_TEXT, IntegerToString(abertasBuy) + " | " + IntegerToString(abertasBuyPositivas));
        ObjectSetString(0, "OrdensV2", OBJPROP_TEXT, IntegerToString(abertasSel) + " | " + IntegerToString(abertasSelPositivas));
        
        ObjectSetString(0, "ProfitV1", OBJPROP_TEXT, DoubleToString(profitBuy, 2));
        ObjectSetString(0, "ProfitV2", OBJPROP_TEXT, DoubleToString(profitSel, 2));
        
        ObjectSetString(0, "PositivoV1", OBJPROP_TEXT, DoubleToString(profitBuyPositivo, 2));
        ObjectSetString(0, "PositivoV2", OBJPROP_TEXT, DoubleToString(profitSelPositivo, 2));      
        
        ObjectSetString(0, "TotalValor", OBJPROP_TEXT, "$ "+DoubleToString(totalProfit, 2));
    }
};

bool CheckNewCandle() {
    datetime currentCandleTime = iTime(_Symbol, _Period, 0);
    if (currentCandleTime != lastCandleTime) {
        lastCandleTime = currentCandleTime;
        return true;
    } else {
        return false;
    }
}

bool IsMarketOpen(string symbol) {
    datetime current_time = TimeCurrent();
    ENUM_SYMBOL_TRADE_MODE trade_mode = (ENUM_SYMBOL_TRADE_MODE)SymbolInfoInteger(symbol, SYMBOL_TRADE_MODE);
    return trade_mode != SYMBOL_TRADE_MODE_DISABLED;
}

bool OpenBuy(CSymbolInfo &Symbol, double entrada, double sl, double tp, const string comment = ""){
    double price = Symbol.Ask();
    double stopLoss = 0.0;
    if(sl>0) stopLoss = price - _Point * sl;
    double takeProfit = 0.0;
    if(tp>0) takeProfit = price + _Point * tp;
    m_trade.PositionOpen(Symbol.Name(), ORDER_TYPE_BUY, AjustaVolume(Symbol, entrada), price, stopLoss, takeProfit, comment);
    return true;
};

bool OpenSel(CSymbolInfo &Symbol, double entrada, double sl, double tp, const string comment = ""){
    double price = Symbol.Bid();
    double stopLoss = 0.0;
    if(sl>0) stopLoss = price + _Point * sl;
    double takeProfit = 0.0;
    if(tp>0) takeProfit = price - _Point * tp;
    m_trade.PositionOpen(Symbol.Name(), ORDER_TYPE_SELL, AjustaVolume(Symbol, entrada), price, stopLoss, takeProfit, comment);
    return true;
};

double AjustaVolume(CSymbolInfo &Symbol, double volume){
    // Limite inferior
    if (volume < minVolume){
        if(Painel) PrintFormat("O volume negociado deve ser maior que %.2f", minVolume);
        return minVolume;
    }

    // Limite superior
    if (volume > maxVolume){
        if(Painel) PrintFormat("O volume negociado deve ser menor que %.2f", maxVolume);
        return maxVolume;
    }

    // Valor Válido
    int ratio = (int)MathRound(volume / stepVolume);
    if ((ratio * stepVolume) != volume){
        if(Painel) PrintFormat("A entrada %.5f é inválida para o ativo %s", volume, Symbol.Name());
        if(Painel) PrintFormat("Nova entrada %.5f para o ativo %s", NormalizeDouble((ratio * stepVolume), Symbol.Digits()), Symbol.Name());
        return NormalizeDouble((ratio * stepVolume), Symbol.Digits());
    }
    return NormalizeDouble(volume, Symbol.Digits());
};

bool IsTradingTime(string startTime, string endTime) {
    long startHour, startMinute, endHour, endMinute;
    StringToTime(startTime, startHour, startMinute);
    StringToTime(endTime, endHour, endMinute);

    datetime tradingStartTime = StringToTime(StringFormat("%d.%02d.%02d %02d:%02d", mqlTime.year, mqlTime.mon, mqlTime.day, startHour, startMinute));
    datetime tradingEndTime = StringToTime(StringFormat("%d.%02d.%02d %02d:%02d", mqlTime.year, mqlTime.mon, mqlTime.day, endHour, endMinute));

    return currentTime >= tradingStartTime && currentTime <= tradingEndTime;
}

void StringToTime(string timeString, long &hour, long &minute) {
    StringReplace(timeString, ":", " ");
    StringToIntegerArray(timeString, hour, minute);
}

void StringToIntegerArray(string str, long &first, long &second) {
    string buffer[2];
    int count = StringSplit(str, ' ', buffer);
    if (count == 2) {
        first = StringToInteger(buffer[0]);
        second = StringToInteger(buffer[0]);
    }
}

bool CheckVolumeValue(double volume_negociado){

    Symbol1.Refresh();

    // Limite inferior
    if (volume_negociado < minVolume)
    {
        PrintFormat("O volume negociado deve ser maior que %.2f", minVolume);
        return false;
    }

    // Limite superior
    if (volume_negociado > maxVolume)
    {
        PrintFormat("O volume negociado deve ser menor que %.2f", maxVolume);
        return false;
    }

    // Valor Válido
    int ratio = (int)MathRound(volume_negociado / stepVolume);
    if ((ratio * stepVolume) != volume_negociado)
    {
        PrintFormat("O volume %.2f é inválido para o ativo %s", volume_negociado, Symbol());
        return false;
    }

    return true;
}

int InitPanel(){
    //---
    string n;
    int linha = 30;
    int yT = 63;
    int yRb = 82;
    int yAc = 82;
    //int ySum = 58;
    
    int linhas = linha * ArraySize(infos);
    int a = linhas + yT + yRb + yAc + 24;
    int l = 400;

    bool t = false; // topo
    bool d = false; // direita
    int ox;
    int oy;
    if(iPosition == CORNER_LEFT_UPPER){
        t = true;
        y = iMarginY; 
        x = iMarginX;
    }
    if(iPosition == CORNER_RIGHT_UPPER){
        t = true;
        d = true;
        y = iMarginY;
        x = iMarginX+l;
    }
    if(iPosition == CORNER_RIGHT_LOWER){
        d = true;
        y = iMarginY+a; 
        x = iMarginX+l;
    }
    if(iPosition == CORNER_LEFT_LOWER){
        y = iMarginY+a; 
        x = iMarginX;
    }
    //CORNER_RIGHT_LOWER
    n = "BG";
    if (ObjectCreate(0,n, OBJ_RECTANGLE_LABEL, 0, 0, 0)){
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);        
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, x);
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, y);
        ObjectSetInteger(0,n, OBJPROP_XSIZE, l);
        ObjectSetInteger(0,n, OBJPROP_YSIZE, a);
        ObjectSetInteger(0,n, OBJPROP_BACK,false);

        ObjectSetInteger(0,n, OBJPROP_BGCOLOR, iColor);
        ObjectSetInteger(0,n, OBJPROP_BORDER_TYPE, BORDER_RAISED);
        ObjectSetInteger(0,n, OBJPROP_BORDER_COLOR, clrRed);
        ObjectSetInteger(0,n, OBJPROP_WIDTH, 5);
    }
    
    n = "BGTitulo";
    if (ObjectCreate(0,n, OBJ_RECTANGLE_LABEL, 0, 0, 0)){
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);     
        if(t){oy=y+6;}else{oy=y-6;}
        if(d){ox=x-6;}else{ox=x+6;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_XSIZE, l - 12);
        ObjectSetInteger(0,n, OBJPROP_YSIZE, yT-8);
        ObjectSetInteger(0,n, OBJPROP_BACK,false);
        ObjectSetInteger(0,n, OBJPROP_BGCOLOR, iColor2);
        ObjectSetInteger(0,n, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0,n, OBJPROP_BORDER_COLOR, iColor);
    }
    n = "Titulo";
    if (ObjectCreate(0,n, OBJ_LABEL, 0, 0, 0)){
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        if(t){oy= y+13;}else{oy= y-13;}
        if(d){ox= x-20;}else{ox= x+20;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_COLOR, iColor3);
        ObjectSetString(0,n, OBJPROP_FONT, "Calibri Bold");
        ObjectSetInteger(0,n, OBJPROP_FONTSIZE, 16);
        ObjectSetInteger(0,n, OBJPROP_BACK,false);
        ObjectSetString(0,n, OBJPROP_TEXT, in_name);
    }
    n = "Par";
    if (ObjectCreate(0,n, OBJ_LABEL, 0, 0, 0)){
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_RIGHT_UPPER);
        if(t){oy= y+22;}else{oy= y-22;}
        if(d){ox= x-l+20;}else{ox= x+l-20;}
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_COLOR, iColor3);
        ObjectSetString(0,n, OBJPROP_FONT, "Calibri Bold");
        ObjectSetInteger(0,n, OBJPROP_FONTSIZE, 9);
        ObjectSetInteger(0,n, OBJPROP_BACK,false);
        ObjectSetString(0,n, OBJPROP_TEXT, Symbol1.Name());
    }
    /*
        n = "BGTotal";
        if (ObjectCreate(0,n, OBJ_RECTANGLE_LABEL, 0, 0, 0))    {
            ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
            if(t){oy= y+a-56;}else{oy= y-a+56;}
            if(d){ox= x-6;}else{ox= x+6;}
            ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
            ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
            ObjectSetInteger(0,n, OBJPROP_XSIZE, l - 12);
            ObjectSetInteger(0,n, OBJPROP_YSIZE, ySum-8);
            ObjectSetInteger(0,n, OBJPROP_BACK,false);

            ObjectSetInteger(0,n, OBJPROP_BGCOLOR, iColor2);
            ObjectSetInteger(0,n, OBJPROP_BORDER_TYPE, BORDER_FLAT);
            ObjectSetInteger(0,n, OBJPROP_BORDER_COLOR, clrWhite);
        }
        n = "Total";
        if (ObjectCreate(0,n, OBJ_LABEL, 0, 0, 0)){
            ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
            ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
            if(t){oy= y+a-46;}else{oy= y-a+46;}
            if(d){ox= x-20;}else{ox= x+20;}
            ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
            ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
            ObjectSetInteger(0,n, OBJPROP_COLOR, iColor3);
            ObjectSetString(0,n, OBJPROP_FONT, "Franklin Gothic Medium");
            ObjectSetInteger(0,n, OBJPROP_FONTSIZE, 12);
            ObjectSetInteger(0,n, OBJPROP_BACK,false);
            ObjectSetString(0,n, OBJPROP_TEXT, "Profit");
        }
        n = "TotalValor";
        if (ObjectCreate(0,n, OBJ_LABEL, 0, 0, 0)){
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_RIGHT_UPPER);
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        if(t){oy= y+a-46;}else{oy= y-a+46;}
        if(d){ox= x-l+16;}else{ox= x+l-16;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_COLOR, clrWhite);
        ObjectSetString(0,n, OBJPROP_FONT, "Franklin Gothic Medium");
        ObjectSetInteger(0,n, OBJPROP_FONTSIZE, 12);
        ObjectSetInteger(0,n, OBJPROP_BACK,false);
        ObjectSetString(0,n, OBJPROP_TEXT, "-");
    }
    */
      
    n = "RbBG";
    if (ObjectCreate(0,n, OBJ_RECTANGLE_LABEL, 0, 0, 0)){
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        if(t){oy= y+yT+4;}else{oy= y-yT-4;}
        if(d){ox= x-6;}else{ox= x+6;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_XSIZE, l - 12);
        ObjectSetInteger(0,n, OBJPROP_YSIZE, yRb-8);
        ObjectSetInteger(0,n, OBJPROP_BACK,false);
        ObjectSetInteger(0,n, OBJPROP_BGCOLOR, iColor);
        ObjectSetInteger(0,n, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0,n, OBJPROP_BORDER_COLOR, clrWhite);
    }
    n = "RbL";
    if (ObjectCreate( 0,n, OBJ_LABEL, 0, 0, 0)){
        ObjectSetString( 0,n, OBJPROP_FONT, "Franklin Gothic Medium");
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        if(t){oy= y+yT+8+4;}else{oy= y-yT-8-4;}
        if(d){ox= x-20;}else{ox= x+20;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_COLOR, iColor3);
        ObjectSetInteger(0,n, OBJPROP_FONTSIZE, 9);
        ObjectSetString( 0,n, OBJPROP_TEXT, "Rebaixamento");
    }
    n = "RbV";
    if (ObjectCreate(0,n, OBJ_LABEL, 0, 0, 0)){
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_RIGHT_UPPER);
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        if(t){oy= y+yT+8+4;}else{oy= y-yT-8-4;}
        if(d){ox= x-l+20;}else{ox= x+l-20;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_COLOR, clrWhite);
        ObjectSetInteger(0,n, OBJPROP_FONTSIZE, 9);
        ObjectSetString(0,n, OBJPROP_TEXT, "-");
    }

    int xBT = l - 40;
    n = "RbBT";
    if (ObjectCreate(0,n, OBJ_RECTANGLE_LABEL, 0, 0, 0)){
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        if(t){oy= y+yT+46;}else{oy= y-yT-46;}
        if(d){ox= x-20;}else{ox= x+20;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_XSIZE, xBT);
        ObjectSetInteger(0,n, OBJPROP_YSIZE, 20);
        ObjectSetInteger(0,n, OBJPROP_BACK,false);

        ObjectSetInteger(0,n, OBJPROP_BGCOLOR, iColor2);
        ObjectSetInteger(0,n, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0,n, OBJPROP_BORDER_COLOR, clrWhite);
    }
    n = "RbBTM";
    if (ObjectCreate(0,n, OBJ_RECTANGLE_LABEL, 0, 0, 0)){
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        if(t){oy= y+yT+46;}else{oy= y-yT-46;}
        if(d){ox= x-20;}else{ox= x+20;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_XSIZE, xBT);
        ObjectSetInteger(0,n, OBJPROP_YSIZE, 20);
        ObjectSetInteger(0,n, OBJPROP_BACK,false);

        ObjectSetInteger(0,n, OBJPROP_BGCOLOR, iColor);
        ObjectSetInteger(0,n, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0,n, OBJPROP_BORDER_COLOR, clrWhite);
    }
    n = "RbBTA";
    if (ObjectCreate(0,n, OBJ_RECTANGLE_LABEL, 0, 0, 0)){
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        if(t){oy= y+yT+46;}else{oy= y-yT-46;}
        if(d){ox= x-20;}else{ox= x+20;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_XSIZE, 1);
        ObjectSetInteger(0,n, OBJPROP_YSIZE, 20);
        ObjectSetInteger(0,n, OBJPROP_BACK,false);

        ObjectSetInteger(0,n, OBJPROP_BGCOLOR, clrCrimson);
        ObjectSetInteger(0,n, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0,n, OBJPROP_BORDER_COLOR, clrWhite);
    }


    // Barra Acmuladora
    n = "AcBG";
    if (ObjectCreate(0,n, OBJ_RECTANGLE_LABEL, 0, 0, 0)){
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        if(t){oy= y+yT+yRb+4;}else{oy= y-yT-yRb-4;}
        if(d){ox= x-6;}else{ox= x+6;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_XSIZE, l - 12);
        ObjectSetInteger(0,n, OBJPROP_YSIZE, yAc-8);
        ObjectSetInteger(0,n, OBJPROP_BACK,false);
        ObjectSetInteger(0,n, OBJPROP_BGCOLOR, iColor);
        ObjectSetInteger(0,n, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0,n, OBJPROP_BORDER_COLOR, clrWhite);
    }
    n = "AcL";
    if (ObjectCreate( 0,n, OBJ_LABEL, 0, 0, 0)){
        ObjectSetString( 0,n, OBJPROP_FONT, "Franklin Gothic Medium");
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        if(t){oy= y+yT+yRb+8+4;}else{oy= y-yT-yRb-8-4;}
        if(d){ox= x-20;}else{ox= x+20;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_COLOR, iColor3);
        ObjectSetInteger(0,n, OBJPROP_FONTSIZE, 9);
        ObjectSetString( 0,n, OBJPROP_TEXT, "Profit");
    }
    n = "AcV";
    if (ObjectCreate(0,n, OBJ_LABEL, 0, 0, 0)){
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_RIGHT_UPPER);
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        if(t){oy= y+yT+yRb+8+4;}else{oy= y-yT-yRb-8-4;}
        if(d){ox= x-l+20;}else{ox= x+l-20;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_COLOR, clrWhite);
        ObjectSetInteger(0,n, OBJPROP_FONTSIZE, 9);
        ObjectSetString(0,n, OBJPROP_TEXT, "-");
    }

    n = "AcBT";
    if (ObjectCreate(0,n, OBJ_RECTANGLE_LABEL, 0, 0, 0)){
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        if(t){oy= y+yT+yRb+46;}else{oy= y-yT-yRb-46;}
        if(d){ox= x-20;}else{ox= x+20;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_XSIZE, xBT);
        ObjectSetInteger(0,n, OBJPROP_YSIZE, 20);
        ObjectSetInteger(0,n, OBJPROP_BACK,false);

        ObjectSetInteger(0,n, OBJPROP_BGCOLOR, iColor2);
        ObjectSetInteger(0,n, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0,n, OBJPROP_BORDER_COLOR, clrWhite);
    }
    n = "AcBTM";
    if (ObjectCreate(0,n, OBJ_RECTANGLE_LABEL, 0, 0, 0)){
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        if(t){oy= y+yT+yRb+46;}else{oy= y-yT-yRb-46;}
        if(d){ox= x-20;}else{ox= x+20;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_XSIZE, 1);
        ObjectSetInteger(0,n, OBJPROP_YSIZE, 20);
        ObjectSetInteger(0,n, OBJPROP_BACK,false);

        ObjectSetInteger(0,n, OBJPROP_BGCOLOR, iColor);
        ObjectSetInteger(0,n, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0,n, OBJPROP_BORDER_COLOR, clrWhite);
    }
    n = "AcBTA";
    if (ObjectCreate(0,n, OBJ_RECTANGLE_LABEL, 0, 0, 0)){
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        if(t){oy= y+yT+yRb+46;}else{oy= y-yT-yRb-46;}
        if(d){ox= x-20;}else{ox= x+20;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_XSIZE, 1);
        ObjectSetInteger(0,n, OBJPROP_YSIZE, 20);
        ObjectSetInteger(0,n, OBJPROP_BACK,false);

        ObjectSetInteger(0,n, OBJPROP_BGCOLOR, clrGreen);
        ObjectSetInteger(0,n, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0,n, OBJPROP_BORDER_COLOR, clrWhite);
    }

    // Criar campos
    for (int i = 0; i < ArraySize(infos); i++) {
        n = infos[i];
        if (!ObjectCreate(0,n, OBJ_LABEL, 0, 0, 0)) return (INIT_FAILED);
        ObjectSetString(0,n, OBJPROP_FONT, "Franklin Gothic Medium");
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);

        if(t){oy= y+yT+yRb+yAc+8+((linhas-linha)-i*linha);}else{oy= y-yT-yRb-yAc-8-(linhas-linha)+i*linha;}
        if(d){ox= x-20;}else{ox= x+20;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);


        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox );

        ObjectSetInteger(0,n, OBJPROP_COLOR, iColor3);
        ObjectSetInteger(0,n, OBJPROP_FONTSIZE, 9);
        ObjectSetString(0,n, OBJPROP_TEXT, infos[i]);
    }

    n = "sep";
    if (ObjectCreate(0,n, OBJ_RECTANGLE_LABEL, 0, 0, 0)) {
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);

        if(t){oy= y+yT+yRb+yAc+8;}else{oy= y-yT-yRb-yAc-8;}
        if(d){ox= x-l+20+130;}else{ox= x+l-20-130;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);

        ObjectSetInteger(0,n, OBJPROP_XSIZE, 1);
        ObjectSetInteger(0,n, OBJPROP_YSIZE, linhas);
        ObjectSetInteger(0,n, OBJPROP_BACK,false);

        ObjectSetInteger(0,n, OBJPROP_BGCOLOR, iColor2);
        ObjectSetInteger(0,n, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0,n, OBJPROP_BORDER_COLOR, iColor2);
    }

    // Iniciar valores
    for (int i = 0; i < ArraySize(infos); i++) {
        n = infos[i] + "V1";
        if (!ObjectCreate(0,n, OBJ_LABEL, 0, 0, 0)) return (INIT_FAILED);
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_RIGHT_UPPER);
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        if(t){oy= y+yT+yRb+yAc+8+((linhas-linha)-i*linha);}else{oy= y-yT-yRb-yAc-8-(linhas-linha)+i*linha;}
        if(d){ox= x-l+20+150;}else{ox= x+l-20-150;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_COLOR, clrWhite);
        ObjectSetInteger(0,n, OBJPROP_FONTSIZE, 9);
        ObjectSetString(0,n, OBJPROP_TEXT, "-");
    }

    // Iniciar valores
    for (int i = 0; i < ArraySize(infos); i++) {
        n = infos[i] + "V2";
        if (!ObjectCreate(0,n, OBJ_LABEL, 0, 0, 0)) return (INIT_FAILED);
        ObjectSetInteger(0,n, OBJPROP_ANCHOR, ANCHOR_RIGHT_UPPER);
        ObjectSetInteger(0,n, OBJPROP_CORNER, iPosition);
        if(t){oy= y+yT+yRb+yAc+8+((linhas-linha)-i*linha);}else{oy= y-yT-yRb-yAc-8-(linhas-linha)+i*linha;}
        if(d){ox= x-l+20;}else{ox= x+l-20;}
        ObjectSetInteger(0,n, OBJPROP_YDISTANCE, oy);
        ObjectSetInteger(0,n, OBJPROP_XDISTANCE, ox);
        ObjectSetInteger(0,n, OBJPROP_COLOR, clrWhite);
        ObjectSetInteger(0,n, OBJPROP_FONTSIZE, 9);
        ObjectSetString(0,n, OBJPROP_TEXT, "-");
    }

    ChartRedraw();

    OnTick();
    return (INIT_SUCCEEDED);
};

void RedrawPanel(){    
    for (int i = 0; i < ArraySize(objs); i++){
        LimpaObj(objs[i]);
    }
    for (int i = 0; i < ArraySize(infos); i++){
        LimpaObj(infos[i]);
        LimpaObj(infos[i] + "V1");
        LimpaObj(infos[i] + "V2");
    }
};

void RemovePanel(){  
    for (int i = 0; i < ArraySize(objs); i++){
        ObjectDelete(0, objs[i]);
    }
    for (int i = 0; i < ArraySize(infos); i++){
        ObjectDelete(0, infos[i]);
        ObjectDelete(0, infos[i] + "V1");
        ObjectDelete(0, infos[i] + "V2");
    }
}

void LimpaObj(string obj){
    ObjectSetInteger(0,obj,OBJPROP_TIMEFRAMES,OBJ_NO_PERIODS);
    ObjectSetInteger(0,obj,OBJPROP_TIMEFRAMES,OBJ_ALL_PERIODS);    
}


double BotResult(datetime time_start){
   double   result = 0.0;
   ulong    ticket;

   if(HistorySelect(time_start, TimeCurrent())){
      for(int i = HistoryDealsTotal() - 1; i >= 0; i--){
         ticket = HistoryDealGetTicket(i);
         if(ticket != 0){
            if(HistoryDealGetInteger(ticket, DEAL_MAGIC) == iMagic && HistoryDealGetString(ticket,DEAL_SYMBOL)==Symbol1.Name()){
                result += HistoryDealGetDouble(ticket, DEAL_PROFIT) + HistoryDealGetDouble(ticket, DEAL_SWAP) + HistoryDealGetDouble(ticket, DEAL_COMMISSION);
            }
           }else{
            Print("Error getting deal ticket in history ...");
            return(EMPTY_VALUE);
            break;
           }
        }
     } else {
      Print("Error getting operations history ...");
      return(EMPTY_VALUE);
     }
    acumulado = result;
    if(acumulado>acumuladoMaximo) acumuladoMaximo=acumulado;
    if(Painel) {                            
        ObjectSetString(0, "AcV", OBJPROP_TEXT, "$ "+DoubleToString(acumulado, 2));
        ObjectSetInteger(0,"AcBTM", OBJPROP_XSIZE, Porcento(rebaixamentoMaximo*2, MathAbs(acumuladoMaximo))*360);
        ObjectSetInteger(0,"AcBTA", OBJPROP_XSIZE, Porcento(rebaixamentoMaximo*2, MathAbs(acumulado))*360);

        if(acumulado<rebaixamentoMaximo/3){
            ObjectSetInteger(0,"AcBTA", OBJPROP_BGCOLOR, clrCrimson);
        }else if(acumulado<rebaixamentoMaximo/2){
            ObjectSetInteger(0,"AcBTA", OBJPROP_BGCOLOR, clrOrangeRed);
        }else if(acumulado<rebaixamentoMaximo){
            ObjectSetInteger(0,"AcBTA", OBJPROP_BGCOLOR, clrGold);
        }else{
            ObjectSetInteger(0,"AcBTA", OBJPROP_BGCOLOR, clrGreen);
        }


    }
   return(result);
  }

double Porcento(int total, double atual){
    if(atual>=total) return (1);
    return (atual/total);
}

void desenhaEvent(string nome, color cor = clrAliceBlue){
    if(!Painel) return;
    string id = nome + " #" + IntegerToString(O);
    ObjectDelete(0, id);
    ObjectCreate(0, id, OBJ_EVENT, 0, TimeCurrent(), 0);
    ObjectSetInteger(0, id, OBJPROP_COLOR, cor);
    ObjectSetString(0, id, OBJPROP_TEXT, nome);
    O++;
}
void desenhaLinhaVertical(string nome, color cor = clrAliceBlue){
    if(!Painel) return;
    nome = nome + " #" + IntegerToString(O);
    ObjectDelete(0, nome);
    ObjectCreate(0, nome, OBJ_VLINE, 0, TimeCurrent(), 0);
    ObjectSetInteger(0, nome, OBJPROP_COLOR, cor);
    O++;
}
void desenhaLinhaHorizontal(string nome, double price, color cor = clrAliceBlue){
    if(!Painel) return;
    ObjectDelete(0, nome);
    ObjectCreate(0, nome, OBJ_HLINE, 0, 0, price);
    ObjectSetInteger(0, nome, OBJPROP_COLOR, cor);
    ObjectSetInteger(0, nome, OBJPROP_WIDTH, 3);
}


