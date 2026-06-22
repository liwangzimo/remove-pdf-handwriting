# remove-pdf-handwriting

一个用于去除 PDF 试卷、练习卷中手写字迹的 Codex 技能。目标是在清理红笔、蓝笔、黑笔批注和解题痕迹的同时，尽量保留原卷的文字、公式、表格、图形、坐标系和统计图。

## 功能

- 自动去除红色、蓝色、绿色、黄色等彩色手写痕迹。
- 支持用局部擦除矩形处理黑色手写痕迹，避免误删黑色印刷文字。
- 支持用恢复矩形找回被自动清理误删的原卷彩色图形。
- 输出干净版 PDF，并生成每页 PNG 预览用于检查。

## 主要文件

- `SKILL.md`：技能说明和处理流程
- `scripts/clean_pdf_handwriting.py`：PDF 清理脚本
- `agents/openai.yaml`：技能 agent 配置
- `vendor/`：随技能打包的 `pymupdf` 和 `Pillow` 依赖

## 基本用法

```powershell
python .\scripts\clean_pdf_handwriting.py `
  --input sample.pdf `
  --output sample_clean.pdf `
  --preview-dir clean_preview
```

使用局部擦除矩形处理黑色手写：

```powershell
python .\scripts\clean_pdf_handwriting.py `
  --input sample.pdf `
  --output sample_clean.pdf `
  --erase-json erase_rects.json
```

使用恢复矩形保留原卷彩色图形：

```powershell
python .\scripts\clean_pdf_handwriting.py `
  --input sample.pdf `
  --output sample_clean.pdf `
  --restore-json restore_rects.json
```

## 矩形配置格式

`erase_rects.json` 和 `restore_rects.json` 都使用页码到矩形列表的映射。页码从 1 开始，矩形坐标是在当前 DPI 渲染结果上的像素坐标：

```json
{
  "1": [
    [410, 400, 720, 720],
    [1828, 700, 1870, 735]
  ]
}
```

## 注意事项

- 坐标依赖 `--dpi` 参数；默认 DPI 是 220。
- 黑色手写不要整页自动删除，因为原卷印刷文字通常也是黑色。
- 自动彩色清理可能误删原卷自带的彩色题图，这时用 `--restore-json` 小范围贴回原图区域。
- 交付前应检查生成的预览图，确认没有大块空白、题干误删或图形破损。
