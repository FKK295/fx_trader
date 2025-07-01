# 取引戦略開発ガイド

このドキュメントでは、FX自動売買システムで使用する取引戦略の開発方法について説明します。

## 目次

- [戦略の基本構造](#戦略の基本構造)
- [バックテストの実行](#バックテストの実行)
- [リスク管理パラメータ](#リスク管理パラメータ)
- [パフォーマンス分析](#パフォーマンス分析)
- [ベストプラクティス](#ベストプラクティス)

## 戦略の基本構造

取引戦略は `backtest/strategies/` ディレクトリにPythonモジュールとして実装します。各戦略は `backtrader.Strategy` を継承する必要があります。

```python
from backtrader import Strategy
import backtrader.indicators as btind

class MyCustomStrategy(Strategy):
    """カスタム取引戦略の例"""
    
    # パラメータ定義
    params = (
        ('sma_fast', 10),    # 短期移動平均線の期間
        ('sma_slow', 30),    # 長期移動平均線の期間
        ('rsi_period', 14),  # RSIの期間
        ('rsi_upper', 70),   # RSIの売りシグナル閾値
        ('rsi_lower', 30),   # RSIの買いシグナル閾値
    )
    
    def __init__(self):
        """インジケーターの初期化"""
        # 移動平均線
        self.sma_fast = btind.SimpleMovingAverage(
            self.data.close, period=self.p.sma_fast)
        self.sma_slow = btind.SimpleMovingAverage(
            self.data.close, period=self.p.sma_slow)
            
        # RSI
        self.rsi = btind.RSI(
            self.data.close, period=self.p.rsi_period)
        
        # クロスオーバーシグナル
        self.crossover = btind.CrossOver(
            self.sma_fast, self.sma_slow)
    
    def next(self):
        """各バーで実行されるロジック"""
        # ポジションを持っていない場合
        if not self.position:
            # ゴールデンクロス + RSIが下限以下で買い
            if self.crossover > 0 and self.rsi < self.p.rsi_lower:
                self.buy()
                
            # デッドクロス + RSIが上限以上で売り
            elif self.crossover < 0 and self.rsi > self.p.rsi_upper:
                self.sell()
        
        # ポジションを持っている場合
        else:
            # 利益確定・損切りのロジック
            if self.crossover < 0 and self.position.size > 0:  # ロングポジションをクローズ
                self.close()
            elif self.crossover > 0 and self.position.size < 0:  # ショートポジションをクローズ
                self.close()
```

## バックテストの実行

戦略をバックテストするには、`backtest/runner.py` を使用します。

```python
from backtest.runner import BacktestRunner

# バックテスト設定
config = {
    'strategy': 'MyCustomStrategy',
    'symbol': 'EUR_USD',
    'timeframe': 'D1',
    'start_date': '2022-01-01',
    'end_date': '2023-01-01',
    'initial_cash': 10000,
    'commission': 0.0005,  # 0.05%の手数料
    'strategy_params': {
        'sma_fast': 10,
        'sma_slow': 30,
        'rsi_period': 14,
        'rsi_upper': 70,
        'rsi_lower': 30,
    }
}

# バックテストの実行
runner = BacktestRunner(config)
results = runner.run()

# 結果の表示
print(f"最終資産: {results['final_value']:.2f}")
print(f"リターン: {results['return_pct']:.2f}%")
print(f"最大ドローダウン: {results['max_drawdown_pct']:.2f}%")
print(f"勝率: {results['win_rate']:.2f}%")
```

## リスク管理パラメータ

戦略には以下のリスク管理パラメータを設定できます：

- `position_size`: ポジションサイズ（口数）
- `stop_loss_pct`: 許容損切幅（％）
- `take_profit_pct`: 利確幅（％）
- `trailing_stop`: トレーリングストップの有効/無効
- `max_drawdown_pct`: 最大ドローダウン許容値（％）

## パフォーマンス分析

バックテスト結果から以下のメトリクスを確認できます：

- **総リターン**: 期間中の総収益率
- **年率リターン**: 年率換算リターン
- **最大ドローダウン**: 最大の資産減少率
- **シャープレシオ**: リスク調整後リターン
- **ソルティノレシオ**: 下方リスク調整後リターン
- **勝率**: 勝ちトレードの割合
- **プロフィットファクター**: 総利益/総損失

## ベストプラクティス

1. **パラメータ最適化**
   - 過剰最適化に注意し、ウォークフォワード分析を実施
   - 複数の時間軸で戦略を検証

2. **リスク管理**
   - 1トレードあたりのリスクを1-2%に制限
   - ストップロスを必ず設定
   - ポートフォリオ全体のリスクを管理

3. **バックテスト**
   - 十分なデータ量でテスト（最低2-3年）
   - スリッページと手数料を考慮
   - アウトオブサンプル検証を実施

4. **モニタリング**
   - 戦略のパフォーマンスを定期的にレビュー
   - 市場環境の変化に応じて戦略を調整
