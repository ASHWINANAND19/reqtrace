import { saveBlob } from './api'

/** Convert a rendered Mermaid SVG to a PNG download (deviation D-4: diagrams are rendered in the browser). */
export async function svgToPng(svg: SVGSVGElement, name: string, scale = 2): Promise<void> {
  const box = svg.viewBox.baseVal
  const width = box?.width || svg.getBoundingClientRect().width
  const height = box?.height || svg.getBoundingClientRect().height
  const clone = svg.cloneNode(true) as SVGSVGElement
  clone.setAttribute('width', String(width))
  clone.setAttribute('height', String(height))
  clone.removeAttribute('style')
  const image = new Image()
  image.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(new XMLSerializer().serializeToString(clone))
  await image.decode()

  const canvas = document.createElement('canvas')
  canvas.width = Math.ceil(width * scale)
  canvas.height = Math.ceil(height * scale)
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('Canvas is not available in this browser.')
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  ctx.scale(scale, scale)
  ctx.drawImage(image, 0, 0, width, height)
  const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/png'))
  if (!blob) throw new Error('Could not create the PNG image.')
  saveBlob(blob, name)
}
