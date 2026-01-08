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

  // Create Menu
  const menu = await prisma.menu.create({
    data: {
      barId: bar.id,
      imageUrl: imageUrl,
      date: new Date()
    }
  })

  // Trigger WhatsApp sending
  await sendMenuviaWhatsApp(menu.id)

  revalidatePath('/')
}

export async function createCompany(formData: FormData) {
  const name = formData.get('name') as string
  const contactName = formData.get('contactName') as string
  const contactPhone = formData.get('contactPhone') as string

  if (!name || !contactPhone) {
    throw new Error('Name and Phone are required')
  }

  await prisma.company.create({
    data: {
      name,
      contactName: contactName || 'Unknown',
      contactPhone
    }
  })

  revalidatePath('/')
}

export async function deleteCompany(id: string) {
  await prisma.company.delete({ where: { id } })
  revalidatePath('/')
}

async function sendMenuviaWhatsApp(menuId: string) {
  const companies = await prisma.company.findMany()
  const menu = await prisma.menu.findUnique({ where: { id: menuId }, include: { bar: true } })
  
  if (!menu) return

  const accountSid = process.env.TWILIO_ACCOUNT_SID
  const authToken = process.env.TWILIO_AUTH_TOKEN
  const fromNumber = process.env.TWILIO_FROM // e.g., 'whatsapp:+14155238886'

  let client;
  if (accountSid && authToken && fromNumber) {
    try {
      client = twilio(accountSid, authToken)
    } catch (error) {
       console.error('Error initializing Twilio client', error)
    }
  } else {
    console.warn('Twilio credentials not found in environment variables. Messages will only be logged.')
  }

  // Construct the message URL
  const appUrl = process.env.APP_URL || 'http://localhost:3000'
  const menuLink = `${appUrl}${menu.imageUrl}`

  console.log('---------------------------------------------------')
  console.log(`STARTING WHATSAPP DISTRIBUTION FOR MENU ${menu.id}`)
  
  for (const company of companies) {
    const messageBody = `Hola ${company.contactName}, *${menu.bar.name}* ha publicado el menú de hoy.`
    
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
