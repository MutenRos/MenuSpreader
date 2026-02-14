'use server'

import { prisma } from '@/lib/prisma'
import { revalidatePath } from 'next/cache'
import fs from 'node:fs/promises'
import path from 'node:path'
import twilio from 'twilio'

export async function uploadMenu(formData: FormData) {
  // Demo: Ensure a bar exists
  let bar = await prisma.bar.findFirst()
  if (!bar) {
    bar = await prisma.bar.create({
      data: {
        name: 'Bar Manolo',
        email: 'manolo@bar.com', 
        menus: { create: [] }
      }
    })
    // Also create some companies if none exist
    const companyCount = await prisma.company.count()
    if (companyCount === 0) {
        await prisma.company.create({
        data: {
            name: 'Tech Corp',
            contactName: 'Alice',
            contactPhone: '+34600000000'
        }
        })
    }
  }

  const file = formData.get('menuFile') as File
  if (!file || file.size === 0) {
    throw new Error('No file uploaded')
  }

  // Save file locally
  const bytes = await file.arrayBuffer()
  const buffer = Buffer.from(bytes)
  
  // Ensure public/uploads exists
  const uploadDir = path.join(process.cwd(), 'public', 'uploads')
  try {
    await fs.mkdir(uploadDir, { recursive: true })
  } catch (e) {
    // ignore
  }
  
  // Sanitize filename
  const filename = `${Date.now()}-${file.name.replace(/[^a-zA-Z0-9.-]/g, '_')}`
  const filepath = path.join(uploadDir, filename)
  
  await fs.writeFile(filepath, buffer)
  
  const imageUrl = `/uploads/${filename}`
  const messageText = formData.get('messageText') as string

  // Create Menu
  const menu = await prisma.menu.create({
    data: {
      barId: bar.id,
      imageUrl: imageUrl,
      date: new Date()
    }
  })

  // Trigger WhatsApp sending
  await sendMenuviaWhatsApp(menu.id, messageText)

  revalidatePath('/')
}

export async function updateBarName(formData: FormData) {
  const name = (formData.get('name') as string)?.trim()
  if (!name || name.length < 2) return  // Mínimo 2 caracteres para el nombre del bar

  const bar = await prisma.bar.findFirst()
  if (bar) {
    await prisma.bar.update({
      where: { id: bar.id },
      data: { name }
    })
  } else {
     // Create if not exists (edge case)
     await prisma.bar.create({
        data: {
            name,
            email: 'placeholder@bar.com'
        }
     })
  }
  revalidatePath('/')
}

export async function createMessageTemplate(formData: FormData) {
  const name = formData.get('name') as string
  const content = formData.get('content') as string
  
  const bar = await prisma.bar.findFirst()
  if (!bar || !name || !content) return

  await prisma.messageTemplate.create({
    data: {
      name,
      content,
      barId: bar.id
    }
  })
  revalidatePath('/')
}

export async function deleteMessageTemplate(id: string) {
  await prisma.messageTemplate.delete({ where: { id } })
  revalidatePath('/')
}

export async function createCompany(formData: FormData) {
  const name = (formData.get('name') as string)?.trim()
  const contactName = (formData.get('contactName') as string)?.trim()
  const contactPhone = (formData.get('contactPhone') as string)?.trim()

  if (!name || !contactPhone) {
    throw new Error('Nombre y teléfono son obligatorios')
  }

  // Validar formato de teléfono (mínimo 9 dígitos)
  const phoneDigits = contactPhone.replace(/\D/g, '')
  if (phoneDigits.length < 9) {
    throw new Error('El teléfono debe tener al menos 9 dígitos')
  }

  await prisma.company.create({
    data: {
      name,
      contactName: contactName || 'Sin nombre',
      contactPhone
    }
  })

  revalidatePath('/')
}

export async function deleteCompany(id: string) {
  await prisma.company.delete({ where: { id } })
  revalidatePath('/')
}

async function sendMenuviaWhatsApp(menuId: string, customMessage?: string) {
  const companies = await prisma.company.findMany()
  const menu = await prisma.menu.findUnique({ where: { id: menuId }, include: { bar: true } })
  
  if (!menu) return

  // Construct the message URL
  const appUrl = process.env.APP_URL || 'http://localhost:3000'
  
  console.log('---------------------------------------------------')
  console.log(`STARTING WHATSAPP DISTRIBUTION FOR MENU ${menu.id}`)
  
  for (const company of companies) {
    // Si hay mensaje personalizado, úsalo. Si no, usa el default.
    // Replace {nombre} with contact name if present in template
    let messageBody = customMessage || `Hola {nombre}, *${menu.bar.name}* ha publicado el menú de hoy.`
    messageBody = messageBody.replace(/{nombre}/g, company.contactName || 'Cliente')
    
    // Usamos la ruta absoluta del sistema de archivos para que el bot la encuentre
    const absoluteImagePath = path.join(process.cwd(), 'public', menu.imageUrl);

    console.log(`[Sending via Bot] To: ${company.contactPhone}`);

    try {
        await fetch('http://localhost:3001/send-menu', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                phone: company.contactPhone,
                caption: messageBody,
                imagePath: absoluteImagePath
            })
        });
        console.log('   -> Request sent to bot server');
    } catch (error) {
        console.error('   -> Failed to contact bot server. Is check_companies.js running?', error);
    }
  }
  console.log('---------------------------------------------------')
}
