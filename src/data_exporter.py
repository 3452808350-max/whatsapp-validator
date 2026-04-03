"""Data export module for CSV and Excel output."""

import os
from typing import List, Dict, Any
import pandas as pd

from .result_aggregator import AggregatedResult
from .config import Config
from .logger import setup_logging

logger = setup_logging()


class DataExporter:
    """
    Exports validation results to CSV and Excel formats.
    
    Features:
    - CSV export with proper encoding
    - Excel export with formatting
    - Summary sheet generation
    """
    
    def __init__(self, config: Config):
        """
        Initialize data exporter.
        
        Args:
            config: Configuration object
        """
        self.config = config
    
    def export(
        self,
        results: List[AggregatedResult],
        output_path: str,
        output_format: str = None,
        include_summary: bool = True
    ) -> str:
        """
        Export results to file.
        
        Args:
            results: List of AggregatedResult objects
            output_path: Path for output file
            output_format: Override format (csv or xlsx)
            include_summary: Whether to include summary sheet (Excel only)
            
        Returns:
            Path to created file
            
        Raises:
            ValueError: If format not supported
        """
        # Determine format
        if output_format:
            fmt = output_format
        else:
            ext = os.path.splitext(output_path)[1].lower().replace('.', '')
            if ext in ['csv', 'xlsx']:
                fmt = ext
            else:
                fmt = self.config.output.format or 'csv'
        
        # Convert to DataFrame
        from .result_aggregator import ResultAggregator
        aggregator = ResultAggregator()
        df = aggregator.to_dataframe(results)
        
        # Create output directory if needed
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        if fmt == 'csv':
            return self._export_csv(df, output_path)
        elif fmt == 'xlsx':
            return self._export_excel(
                df, 
                output_path, 
                results, 
                include_summary
            )
        else:
            raise ValueError(f"Unsupported output format: {fmt}")
    
    def _export_csv(self, df: pd.DataFrame, output_path: str) -> str:
        """
        Export to CSV file.
        
        Args:
            df: DataFrame to export
            output_path: Path for output file
            
        Returns:
            Path to created file
        """
        df.to_csv(output_path, index=False, encoding='utf-8')
        logger.info(f"Exported {len(df)} rows to CSV: {output_path}")
        return output_path
    
    def _export_excel(
        self,
        df: pd.DataFrame,
        output_path: str,
        results: List[AggregatedResult],
        include_summary: bool = True
    ) -> str:
        """
        Export to Excel file with formatting.
        
        Args:
            df: DataFrame to export
            output_path: Path for output file
            results: Original results for summary
            include_summary: Whether to include summary sheet
            
        Returns:
            Path to created file
        """
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Write main results
            df.to_excel(writer, sheet_name='Results', index=False)
            
            # Write summary if requested
            if include_summary:
                summary_df = self._create_summary_df(results)
                summary_df.to_excel(
                    writer, 
                    sheet_name='Summary', 
                    index=False
                )
            
            # Auto-adjust column widths
            self._adjust_column_widths(writer)
        
        logger.info(f"Exported {len(df)} rows to Excel: {output_path}")
        return output_path
    
    def _create_summary_df(
        self, 
        results: List[AggregatedResult]
    ) -> pd.DataFrame:
        """
        Create summary DataFrame.
        
        Args:
            results: List of AggregatedResult objects
            
        Returns:
            DataFrame with summary statistics
        """
        from .result_aggregator import ResultAggregator
        aggregator = ResultAggregator()
        summary = aggregator.generate_summary(results)
        
        rows = []
        for key, value in summary.items():
            rows.append({
                'Metric': key.replace('_', ' ').title(),
                'Value': value
            })
        
        return pd.DataFrame(rows)
    
    def _adjust_column_widths(self, writer: pd.ExcelWriter) -> None:
        """Adjust column widths in Excel file."""
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)  # Cap at 50
                worksheet.column_dimensions[column_letter].width = adjusted_width
